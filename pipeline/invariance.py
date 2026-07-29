"""
Phase 16 — First-principles invariance metric (biology-to-nuisance).

Idea: a good pathology encoder honors the transformations tissue itself is invariant to
— exact dihedral SYMMETRIES (rotation/reflection: tissue has no canonical orientation) and
STAIN perturbation (a lab/scanner nuisance). For a patch x and a nuisance view T(x):
  is f(T(x)) closer to f(x) than to a DIFFERENT patch?
If yes, the encoder collapses nuisance while keeping distinct tissue apart = good.

Clean embedding = cached PATCH_Features (both cache and fresh go through center_square,
so they are consistent). Transformed views are RE-EMBEDDED (needs the encoder = GPU).

Per (dataset, encoder, transform):
  recall@1     : fraction where f(T(x_i)) retrieves its own clean x_i as top-1 (over N clean)
  recall@10    : fraction where x_i is within top-10 of f(T(x_i))
  retention@10 : |kNN_clean(x_i) ∩ kNN_of_f(T(x_i))| / 10  (neighborhood preservation)
  align_dist   : mean cosine distance d(f(x_i), f(T(x_i)))            (nuisance shift, ↓ good)
  bio_spread   : mean cosine distance to random other patches         (biological scale)
  ratio        : bio_spread / align_dist  (biology moves the embedding more than nuisance, ↑ good)

One encoder per call (SLURM array). GPU.
"""
import os, sys, time, argparse
import numpy as np, pandas as pd, h5py, torch
from PIL import Image, ImageFile
from torch.utils.data import Dataset, DataLoader
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import normalize
ImageFile.LOAD_TRUNCATED_IMAGES = True
sys.path.insert(0, "/path/to/external")               # external: the patch-extraction module
from extract_patches import center_square, read_metadata, DEF_BASE
from utils import augment as ap
from config import FEAT, OUT


class TfDS(Dataset):
    def __init__(self, data_dir, rows, transform, tfn, seed):
        self.d, self.rows, self.t, self.tfn, self.seed = data_dir, rows, transform, tfn, seed
    def __len__(self): return len(self.rows)
    def __getitem__(self, i):
        img = Image.open(os.path.join(self.d, self.rows[i]["filepath"])).convert("RGB")
        img = center_square(img)
        img = self.tfn(img, np.random.default_rng(self.seed + i))
        return self.t(img), i


def embed(enc, ds_obj, bs, precision):
    dl = DataLoader(ds_obj, batch_size=bs, num_workers=4, shuffle=False, pin_memory=True)
    out = []
    with torch.inference_mode(), torch.autocast("cuda", dtype=precision):
        for x, _ in dl:
            out.append(enc(x.cuda(non_blocking=True)).float().cpu().numpy())
    return np.concatenate(out)


def soft_js_invariance(Zc, Zt, tau=0.1):
    """Probabilistic (soft) neighbourhood invariance: JS divergence between the SNE-style
    neighbour distributions of the clean vs transformed view (over the clean set, self excluded).
    Returns mean_i exp(-JS_i) in (0.5,1]; higher = distributions agree = more invariant."""
    Scc = Zc @ Zc.T
    Stc = Zt @ Zc.T
    np.fill_diagonal(Scc, -np.inf)
    np.fill_diagonal(Stc, -np.inf)
    def softmax(S):
        S = S / tau; S = S - S.max(1, keepdims=True); e = np.exp(S); return e / e.sum(1, keepdims=True)
    P = softmax(Scc); Q = softmax(Stc); M = 0.5 * (P + Q)
    js = 0.5 * (P * np.log(np.where(P > 0, P / M, 1.0))).sum(1) \
       + 0.5 * (Q * np.log(np.where(Q > 0, Q / M, 1.0))).sum(1)
    return float(np.mean(np.exp(-js)))


def main():
    P = argparse.ArgumentParser()
    P.add_argument("--encoder", required=True)
    P.add_argument("--datasets", nargs="+",
                   default=["MHIST", "CHAOYANG", "Kather-MSI-CRC", "Kather-MSI-STAD", "TCGA-TILs"])
    P.add_argument("--n", type=int, default=4000)
    P.add_argument("--k", type=int, default=10)
    P.add_argument("--bs", type=int, default=128)
    P.add_argument("--seed", type=int, default=42)
    P.add_argument("--save_emb", action="store_true", help="save transformed embeddings (fp16) for CPU re-use")
    P.add_argument("--emb_dir", default="/path/to/emb_cache")
    a = P.parse_args()

    from trident.patch_encoder_models.load import encoder_factory
    enc = encoder_factory(a.encoder); enc.eval().cuda()
    transform, precision = enc.eval_transforms, enc.precision
    bs = 64 if a.encoder == "musk" else a.bs
    rows_out = []
    t0 = time.time()

    for ds in a.datasets:
        meta = read_metadata(os.path.join(DEF_BASE, ds, "metadata.csv"))
        n_meta = len(meta)
        h5p = os.path.join(FEAT, ds, f"features_{a.encoder}.h5")
        if not os.path.exists(h5p):
            print(f"  [skip] {ds}: no cached features"); continue
        with h5py.File(h5p, "r") as f:
            if f["features"].shape[0] != n_meta:
                print(f"  [skip] {ds}: len mismatch"); continue
            Zc_full = f["features"][:]
        rng = np.random.default_rng(a.seed)
        idx = np.sort(rng.choice(n_meta, min(a.n, n_meta), replace=False))
        Zc = normalize(Zc_full[idx].astype("float32"), axis=1)
        sub_rows = [meta[i] for i in idx]
        N = len(idx)

        nbr = NearestNeighbors(n_neighbors=a.k + 1, metric="cosine", n_jobs=-1).fit(Zc)
        N_clean = nbr.kneighbors(Zc, return_distance=False)[:, 1:]
        clean_sets = [set(r.tolist()) for r in N_clean]
        # biological scale: mean cosine distance to random other patches
        perm = rng.permutation(N)
        bio_spread = float(np.mean(1.0 - np.sum(Zc * Zc[perm], axis=1)))

        edir = os.path.join(a.emb_dir, a.encoder)
        if a.save_emb:
            os.makedirs(edir, exist_ok=True)
            np.save(os.path.join(edir, f"{ds}_clean.npy"), Zc.astype("float16"))

        for tname, tfn in ap.INVARIANCE_TRANSFORMS.items():
            Zt = normalize(embed(enc, TfDS(os.path.join(DEF_BASE, ds), sub_rows, transform, tfn, a.seed),
                                 bs, precision), axis=1)
            if a.save_emb:
                np.save(os.path.join(edir, f"{ds}_{tname}.npy"), Zt.astype("float16"))
            I = nbr.kneighbors(Zt, return_distance=False)     # neighbors of transformed view in clean set
            r1 = np.mean([I[i][0] == i for i in range(N)])
            rk = np.mean([i in I[i][:a.k] for i in range(N)])
            ret = np.mean([len(set([x for x in I[i] if x != i][:a.k]) & clean_sets[i]) / a.k
                           for i in range(N)])
            align = float(np.mean(1.0 - np.sum(Zc * Zt, axis=1)))
            sjs = soft_js_invariance(Zc, Zt)                  # probabilistic (soft) invariance
            rows_out.append({"dataset": ds, "encoder": a.encoder, "transform": tname,
                             "recall@1": float(r1), "recall@10": float(rk),
                             "retention@10": float(ret), "soft_js": sjs, "align_dist": align,
                             "bio_spread": bio_spread, "ratio": bio_spread / (align + 1e-9),
                             "n": N})
            print(f"  {ds:16s} {tname:10s} r@1={r1:.3f} ret={ret:.3f} soft_js={sjs:.3f} "
                  f"align={align:.4f}", flush=True)

    df = pd.DataFrame(rows_out)
    os.makedirs(OUT, exist_ok=True)
    outp = os.path.join(OUT, f"phase16_invariance_{a.encoder}.csv")
    df.to_csv(outp, index=False)
    print(f"\n[SAVED] {outp}  ({len(df)} rows, {time.time()-t0:.0f}s)")


if __name__ == "__main__":
    main()
