"""
Build the master per-encoder metrics table -> results/encoder_metrics.csv.

One row per encoder with every axis the paper uses, assembled from the primary artifacts:
  retention   : rotation invariance (retention@10, mean over rot90/180/270 & 16 datasets)  [invariance]
  ret_hflip   : hflip-control retention (near-null)                                          [invariance]
  ret_stain   : stain-control retention (near-null)                                          [invariance]
  effrank     : discriminability (RankMe effective rank, recomputed from cached features)
  Q_vmf       : vMF log-likelihood-ratio quality (dimension-robust)                          [probabilistic]
  auc         : downstream oracle (patient-grouped linear probe, mean over 16 datasets)      [linear_probe_oracle]
  auc_knn     : second oracle (kNN probe), if available                                      [knn]
  combined    : z(retention) + z(effrank)  (z over the invariance roster)
  family, dim

Everything downstream (top-k/regret, hero scatter, leaderboard, ablation, mechanism) reads this.
"""
import os, glob
import numpy as np, pandas as pd, h5py
from _common import ROOT, zscore                      # noqa: E402  (path bootstrap)
from config import OUT, FEAT, FAMILY, VLM
import sys; sys.path.insert(0, os.path.join(ROOT))
from utils import intrinsic as im

ROT = ["rot90", "rot180", "rot270"]


def _effrank(enc, datasets, sub=3000, seed=123):
    rng = np.random.default_rng(seed); ers = []
    for ds in datasets:
        p = os.path.join(FEAT, ds, f"features_{enc}.h5")
        if not os.path.exists(p): continue
        with h5py.File(p, "r") as f:
            n = f["features"].shape[0]
            idx = np.sort(rng.choice(n, min(sub, n), replace=False))
            ers.append(im.effective_rank(f["features"][:][idx].astype("float32")))
    return float(np.mean(ers)) if ers else np.nan


def build():
    # --- invariance (invariance) ---
    d16 = pd.concat([pd.read_csv(f) for f in glob.glob(os.path.join(OUT, "invariance_*.csv"))
                     if "summary" not in f], ignore_index=True)
    ret_r = lambda tf: d16[d16["transform"].isin(tf)].groupby("encoder")["retention@10"].mean()
    retention = ret_r(ROT); ret_hflip = ret_r(["hflip"]); ret_stain = ret_r(["stain_hed"])
    datasets = sorted(d16.dataset.unique())

    # --- oracle (linear_probe_oracle) + kNN oracle (knn) ---
    auc = pd.read_csv(os.path.join(OUT, "linear_probe_oracle_scores.csv")).groupby("encoder").auc.mean()
    knn_p = os.path.join(OUT, "knn_probe_oracle_scores.csv")
    auc_knn = (pd.read_csv(knn_p).groupby("encoder").knn_auc.mean()
               if os.path.exists(knn_p) else pd.Series(dtype=float))

    # --- vMF (probabilistic_prob_scores) ---
    vmf_p = os.path.join(OUT, "probabilistic_prob_scores.csv")
    Q_vmf = (pd.read_csv(vmf_p).groupby("encoder").Q_vmf.mean()
             if os.path.exists(vmf_p) else pd.Series(dtype=float))

    # --- effrank + dim (recompute from cached features, all encoders that have them) ---
    encs = sorted(retention.index)                     # invariance roster
    eff, dim = {}, {}
    for e in encs:
        eff[e] = _effrank(e, datasets)
        p = glob.glob(os.path.join(FEAT, "*", f"features_{e}.h5"))
        with h5py.File(p[0], "r") as f: dim[e] = f["features"].shape[1]

    T = pd.DataFrame({"retention": retention, "ret_hflip": ret_hflip, "ret_stain": ret_stain,
                      "effrank": pd.Series(eff), "Q_vmf": Q_vmf, "auc": auc, "auc_knn": auc_knn,
                      "dim": pd.Series(dim)})
    T = T.loc[encs]                                    # invariance roster order
    T["family"] = [FAMILY.get(e, "?") for e in T.index]
    T["is_vlm"] = [e in VLM for e in T.index]
    T["combined"] = zscore(T["retention"]) + zscore(T["effrank"])   # z over the roster
    T.index.name = "encoder"
    out = os.path.join(OUT, "encoder_metrics.csv"); T.to_csv(out)
    print(f"[SAVED] {out}  ({len(T)} encoders x {T.shape[1]} cols; {len(datasets)} datasets)")
    return T


if __name__ == "__main__":
    from scipy.stats import spearmanr
    T = build()
    vo = T[~T.is_vlm]
    print("\nsanity (vision-only, n=%d):" % len(vo))
    for m in ["retention", "effrank", "combined", "Q_vmf"]:
        r, p = spearmanr(vo[m], vo.auc); print(f"  {m:10s} ~ auc  rho={r:+.3f}  p={p:.4f}")
