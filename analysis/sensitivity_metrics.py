"""
Ablation #10 (discriminability measure) + #12 (data efficiency).

Recomputes per-(encoder,dataset) intrinsic measures on cached features (vision-only), then:
  #10  for each discriminability measure (effrank, effrank/d, alpha-ReQ, TwoNN-id, -uniformity,
       coding-rate, coding-rate/d): combined z(retention)+z(measure) ~ downstream. The effrank/d
       ('effrank_norm') row is the direct answer to the dimension-confound objection.
  #12  vary the number of UNLABELLED datasets the metric is computed on (1,2,4,8,16); over random
       subsets, correlate the (retention+effrank) score vs the FULL 16-dataset oracle -> how much
       unlabelled data the ranking needs.
Outputs: results/intrinsic_per_dataset.csv, results/sensitivity_datasets.csv + printed tables.
"""
import os, glob
import numpy as np, pandas as pd, h5py
from scipy.stats import spearmanr
from _common import load_metrics, vision_only, zscore
from config import OUT, FEAT, VLM
import sys; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import intrinsic as im

ROT = ["rot90", "rot180", "rot270"]
MEAS = ["I_effrank", "I_effrank_norm", "I_alpha_req", "I_twonn_id",
        "I_neg_uniformity", "I_coding_rate", "I_coding_rate_norm"]


def per_dataset_intrinsic(encs, datasets, sub=3000, seed=123):
    rng = np.random.default_rng(seed); rows = []
    for e in encs:
        for ds in datasets:
            p = os.path.join(FEAT, ds, f"features_{e}.h5")
            if not os.path.exists(p): continue
            with h5py.File(p, "r") as f:
                n = f["features"].shape[0]
                idx = np.sort(rng.choice(n, min(sub, n), replace=False))
                Z = f["features"][:][idx].astype("float32")
            rows.append({"encoder": e, "dataset": ds, **im.all_intrinsic(Z)})
        print(f"  intrinsic done {e}", flush=True)
    return pd.DataFrame(rows)


def run():
    T = vision_only(load_metrics()); auc = T.auc
    d16 = pd.concat([pd.read_csv(f) for f in glob.glob(os.path.join(OUT, "phase16_invariance_*.csv"))
                     if "summary" not in f], ignore_index=True)
    d16 = d16[~d16.encoder.isin(VLM)]
    ret_pd = d16[d16["transform"].isin(ROT)].groupby(["dataset", "encoder"])["retention@10"].mean()  # per ds
    datasets = sorted(d16.dataset.unique())

    I = per_dataset_intrinsic(list(T.index), datasets)
    I.to_csv(os.path.join(OUT, "intrinsic_per_dataset.csv"), index=False)

    # ---- #10 discriminability-measure ablation (mean over 16 datasets) ----
    ret16 = ret_pd.groupby("encoder").mean().reindex(T.index)
    print("\n=== #10 discriminability measure (combined with retention@10, vision-only) ===")
    print("   measure            alone    +retention")
    for mcol in MEAS:
        s = I.groupby("encoder")[mcol].mean().reindex(T.index)
        alone = spearmanr(s, auc, nan_policy="omit")[0]
        comb = spearmanr(zscore(ret16) + zscore(s), auc, nan_policy="omit")[0]
        mark = "  <<< used (effrank)" if mcol == "I_effrank" else ("  <- dim-normalized" if mcol == "I_effrank_norm" else "")
        print(f"   {mcol:18s} {alone:+.3f}    {comb:+.3f}{mark}")

    # ---- #12 data efficiency: how many unlabelled datasets does the metric need? ----
    eff_pd = I.set_index(["encoder", "dataset"])["I_effrank"]
    rng = np.random.default_rng(0); rows = []
    print("\n=== #12 data efficiency: (retention+effrank) on d datasets ~ FULL oracle ===")
    for d in [1, 2, 4, 8, 16]:
        rr = []
        for _ in range(40 if d < 16 else 1):
            dss = rng.choice(datasets, d, replace=False)
            r = ret_pd[ret_pd.index.get_level_values("dataset").isin(dss)].groupby("encoder").mean().reindex(T.index)
            ef = eff_pd[eff_pd.index.get_level_values("dataset").isin(dss)].groupby("encoder").mean().reindex(T.index)
            q = zscore(r) + zscore(ef)
            rr.append(spearmanr(q, auc, nan_policy="omit")[0])
        rows.append({"n_datasets": d, "rho_mean": np.mean(rr), "rho_sd": np.std(rr)})
        print(f"   d={d:2d} datasets   ρ = {np.mean(rr):+.3f} ± {np.std(rr):.3f}")
    pd.DataFrame(rows).to_csv(os.path.join(OUT, "sensitivity_datasets.csv"), index=False)
    print("\n[SAVED] results/intrinsic_per_dataset.csv + results/sensitivity_datasets.csv")


if __name__ == "__main__":
    run()
