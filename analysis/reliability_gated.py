"""
Reliability-gating: INVEX predicts downstream only as well as the oracle is itself rankable.

The per-encoder INVEX (combined) score is FIXED. We vary which downstream datasets define the oracle,
ordered by how much they separate encoders (AUC spread across the vision-only roster), and correlate.
  * cumulative curve: add datasets most-separated-first vs most-saturated-first -> ρ(k). The two
    curves converge at k=16 (=full oracle); the gap IS the reliability-gating.
  * per-dataset scatter: within-dataset ρ vs that dataset's AUC spread (separation necessary,
    not sufficient — task-idiosyncratic datasets like BreaKHis are labelled outliers).
This is attenuation by criterion unreliability: a saturated oracle caps ρ near 0 regardless of INVEX.
Outputs: figures/reliability_gated.png, results/reliability_gated.csv
"""
import os, glob
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from scipy.stats import spearmanr
from _common import load_metrics, vision_only, FIGDIR
from config import OUT, VLM

ROT = ["rot90", "rot180", "rot270"]


def run():
    T = vision_only(load_metrics())                       # per-encoder combined + retention (fixed)
    sc = pd.read_csv(os.path.join(OUT, "linear_probe_oracle_scores.csv"))
    auc = sc[~sc.encoder.isin(VLM)][["dataset", "encoder", "auc"]]
    spread = auc.groupby("dataset").auc.agg(lambda s: s.max() - s.min()).sort_values(ascending=False)

    # per-dataset within-dataset invariance->AUC rho (for the scatter)
    d16 = pd.concat([pd.read_csv(f) for f in glob.glob(os.path.join(OUT, "invariance_*.csv"))
                     if "summary" not in f], ignore_index=True)
    ret = d16[d16["transform"].isin(ROT)].groupby(["dataset", "encoder"])["retention@10"].mean().reset_index()
    m = ret.merge(auc, on=["dataset", "encoder"])
    pdrho = {}
    for ds, g in m.groupby("dataset"):
        g = g.dropna()
        pdrho[ds] = spearmanr(g["retention@10"], g.auc)[0] if g.auc.nunique() >= 3 else np.nan

    def oracle_rho(dss):
        o = auc[auc.dataset.isin(dss)].groupby("encoder").auc.mean()
        j = T.join(o.rename("o")).dropna(subset=["o", "combined"])
        return spearmanr(j.combined, j.o)[0] if j.o.nunique() >= 3 else np.nan

    order_sep = list(spread.index)                        # most-separated first
    ks = list(range(2, len(order_sep) + 1))
    rho_desc = [oracle_rho(order_sep[:k]) for k in ks]           # add separated first
    rho_asc = [oracle_rho(order_sep[::-1][:k]) for k in ks]      # add saturated first
    pd.DataFrame({"k": ks, "rho_add_separated_first": rho_desc,
                  "rho_add_saturated_first": rho_asc}).to_csv(os.path.join(OUT, "reliability_gated.csv"), index=False)

    # --- figure ---
    fig, ax = plt.subplots(1, 2, figsize=(12.5, 4.6))
    ax[0].plot(ks, rho_desc, "-o", ms=4, color="#2b6cb0", label="add most-separated datasets first")
    ax[0].plot(ks, rho_asc, "-o", ms=4, color="#c53030", label="add most-saturated datasets first")
    ax[0].axhline(oracle_rho(order_sep), ls="--", color="grey", lw=0.9, label="full 16-dataset oracle")
    ax[0].axhline(0, color="k", lw=0.5)
    ax[0].set_xlabel("number of datasets in the oracle"); ax[0].set_ylabel("INVEX ρ vs oracle")
    ax[0].set_title("Reliability-gating: ρ depends on which datasets\ncan actually rank encoders")
    ax[0].legend(fontsize=8, loc="lower center")

    sx = [spread[ds] for ds in pdrho]; sy = [pdrho[ds] for ds in pdrho]
    ax[1].scatter(sx, sy, s=70, c="#2b6cb0", edgecolor="k", linewidth=0.4)
    for ds in pdrho:
        if spread[ds] > 0.08 and pdrho[ds] < 0.2:          # separated-but-missed outliers
            ax[1].annotate(ds, (spread[ds], pdrho[ds]), fontsize=7, color="#c53030",
                           xytext=(4, 2), textcoords="offset points")
    ax[1].axhline(0, color="k", lw=0.5); ax[1].axvline(0.03, ls=":", color="grey", lw=0.8)
    ax[1].text(0.031, ax[1].get_ylim()[0] + 0.02, "saturated →", fontsize=7, color="grey")
    ax[1].set_xlabel("dataset AUC spread (encoder separation)")
    ax[1].set_ylabel("within-dataset invariance→AUC ρ")
    ax[1].set_title("Separation is necessary, not sufficient\n(labelled: separated but INVEX misses)")
    fig.tight_layout(); p = os.path.join(FIGDIR, "reliability_gated.png"); fig.savefig(p, dpi=150)

    # --- printed summary ---
    disc = spread[spread >= spread.median()].index; sat = spread[spread < spread.median()].index
    print(f"[SAVED] {p} + results/reliability_gated.csv\n")
    print("=== reliability-gating (INVEX combined, vision-only) ===")
    print(f"  full 16-dataset oracle        ρ = {oracle_rho(spread.index):+.3f}")
    print(f"  discriminating half (n_ds=8)  ρ = {oracle_rho(disc):+.3f}")
    print(f"  saturated half (n_ds=8)       ρ = {oracle_rho(sat):+.3f}")
    print("\n  monotone (top-k most-separated datasets only):")
    for k in [2, 4, 6, 8, 12, 16]:
        if k <= len(order_sep): print(f"    top-{k:2d} datasets  ρ = {oracle_rho(order_sep[:k]):+.3f}")
    print(f"\n  corr(dataset spread, within-dataset ρ) = "
          f"{spearmanr([spread[d] for d in pdrho if not np.isnan(pdrho[d])], [pdrho[d] for d in pdrho if not np.isnan(pdrho[d])])[0]:+.3f}")


if __name__ == "__main__":
    run()
