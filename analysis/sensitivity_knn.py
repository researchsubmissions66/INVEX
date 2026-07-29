"""
Sensitivity of the headline to the invariance subsampling (N) and neighborhood size (k),
recomputed on the banked fp16 embeddings (emb_cache/) — no re-embedding needed.

For each vision-only encoder x dataset: load clean + rot90/180/270 views, recompute retention@k
across a grid of (k, N, seed), aggregate per encoder (mean over rot & datasets), then correlate
z(retention)+z(effrank) with the downstream oracle. effrank is held at its master-table value.
Outputs: results/sensitivity_kN.csv + printed table.
"""
import os, glob
import numpy as np, pandas as pd
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import normalize
from scipy.stats import spearmanr
from _common import load_metrics, vision_only, zscore
from config import OUT, ROOT

EMB = os.path.join(ROOT, "emb_cache")
ROT = ["rot90", "rot180", "rot270"]
KS = [5, 10, 20, 50, 100]
NS = [500, 1000, 2000, 4000]
SEEDS = [42, 1, 7]


def retention_grid(clean, views, kmax, N, seed):
    """retention@k for k in KS on a size-N subsample; returns dict k->mean retention over views."""
    rng = np.random.default_rng(seed)
    n = len(clean)
    idx = np.sort(rng.choice(n, min(N, n), replace=False)) if N < n else np.arange(n)
    Zc = normalize(clean[idx].astype("float32"), axis=1)
    nbr = NearestNeighbors(n_neighbors=kmax + 1, metric="cosine", n_jobs=-1).fit(Zc)
    Ic = nbr.kneighbors(Zc, return_distance=False)[:, 1:]           # clean neighborhoods (self excl)
    clean_sets = {k: [set(r[:k]) for r in Ic] for k in KS}
    out = {k: [] for k in KS}
    for V in views:
        Zt = normalize(V[idx].astype("float32"), axis=1)
        It = nbr.kneighbors(Zt, return_distance=False)
        for k in KS:
            ret = np.mean([len(set([x for x in It[i] if x != i][:k]) & clean_sets[k][i]) / k
                           for i in range(len(Zt))])
            out[k].append(ret)
    return {k: float(np.mean(v)) for k, v in out.items()}


def run():
    T = vision_only(load_metrics()); eff = T.effrank; auc = T.auc
    encs = [e for e in T.index if os.path.isdir(os.path.join(EMB, e))]
    dsets = sorted({os.path.basename(f)[:-len("_clean.npy")]
                    for f in glob.glob(os.path.join(EMB, encs[0], "*_clean.npy"))})
    print(f"emb_cache: {len(encs)} vision-only encoders x {len(dsets)} datasets", flush=True)

    rows = []
    # (a) k-sweep at N=4000 seed=42 ; (b) N-sweep at k=10 ; (c) seed spread at k=10,N=2000
    for e in encs:
        per_ds = {}
        for ds in dsets:
            try:
                clean = np.load(os.path.join(EMB, e, f"{ds}_clean.npy"))
                views = [np.load(os.path.join(EMB, e, f"{ds}_{t}.npy")) for t in ROT]
            except FileNotFoundError:
                continue
            for N in NS:
                for seed in (SEEDS if N == 2000 else [42]):
                    key = (N, seed)
                    g = retention_grid(clean, views, max(KS), N, seed)
                    per_ds.setdefault(key, []).append(g)
        for (N, seed), gl in per_ds.items():
            agg = {k: np.mean([g[k] for g in gl]) for k in KS}
            rows.append({"encoder": e, "N": N, "seed": seed, **{f"ret@{k}": agg[k] for k in KS}})
        print(f"  done {e}", flush=True)

    R = pd.DataFrame(rows); R.to_csv(os.path.join(OUT, "sensitivity_kN.csv"), index=False)

    def rho_for(sub, kcol):
        s = sub.set_index("encoder")[kcol].reindex(auc.index)
        return spearmanr(zscore(s) + zscore(eff.reindex(auc.index)), auc.reindex(s.index), nan_policy="omit")[0]

    base = R[(R.N == 4000) & (R.seed == 42)]
    print("\n=== k-sweep (N=4000): combined ρ vs downstream ===")
    for k in KS: print(f"    retention@{k:<3d} + effrank   ρ={rho_for(base, f'ret@{k}'):+.3f}")
    print("\n=== N-sweep (k=10, seed=42): combined ρ ===")
    for N in NS:
        sub = R[(R.N == N) & (R.seed == 42)]
        print(f"    N={N:<4d}   ρ={rho_for(sub, 'ret@10'):+.3f}")
    print("\n=== seed spread (k=10, N=2000) ===")
    rr = [rho_for(R[(R.N == 2000) & (R.seed == s)], "ret@10") for s in SEEDS]
    print(f"    seeds {SEEDS} → ρ = {[round(x,3) for x in rr]}   (mean {np.mean(rr):+.3f}, sd {np.std(rr):.3f})")
    print(f"\n  headline reference: retention@10, N=4000, seed=42 → ρ={rho_for(base,'ret@10'):+.3f}")


if __name__ == "__main__":
    run()
