"""
Parameter sensitivity of the headline (combined ~ downstream, vision-only, Spearman rho).

Instant sweeps (from banked per-encoder scores; no re-embedding):
  A. combination weight   Q(alpha) = alpha*z(retention) + (1-alpha)*z(effrank), alpha in [0,1]
  B. invariance operationalization: retention@10 vs recall@1/@10 vs soft_js vs ratio (alone + combined)
The k / N / SUB sweeps that need the banked embeddings live in analysis/sensitivity_knn_probe_oracle.py.
Outputs: figures/sensitivity.png, results/sensitivity_alpha.csv
"""
import os, glob
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from scipy.stats import spearmanr
from _common import load_metrics, vision_only, zscore, FIGDIR
from config import OUT, VLM

ROT = ["rot90", "rot180", "rot270"]


def run():
    T = vision_only(load_metrics())
    auc = T.auc

    # --- A. combination-weight sweep ---
    alphas = np.linspace(0, 1, 21)
    rz, ez = zscore(T.retention), zscore(T.effrank)
    rho_a = [spearmanr(a * rz + (1 - a) * ez, auc)[0] for a in alphas]
    pd.DataFrame({"alpha": alphas, "rho": rho_a}).to_csv(os.path.join(OUT, "sensitivity_alpha.csv"), index=False)
    best_a = alphas[int(np.argmax(rho_a))]

    # --- B. invariance operationalization (mean over rot & datasets), alone + combined with effrank ---
    d16 = pd.concat([pd.read_csv(f) for f in glob.glob(os.path.join(OUT, "invariance_*.csv"))
                     if "summary" not in f], ignore_index=True)
    d16 = d16[~d16.encoder.isin(VLM)]
    ops = {}
    for col, name in [("retention@10", "retention@10"), ("recall@1", "recall@1"),
                      ("recall@10", "recall@10"), ("soft_js", "soft_js"), ("ratio", "ratio")]:
        if col not in d16: continue
        s = d16[d16["transform"].isin(ROT)].groupby("encoder")[col].mean().reindex(T.index)
        alone = spearmanr(s, auc, nan_policy="omit")[0]
        comb = spearmanr(zscore(s) + zscore(T.effrank), auc, nan_policy="omit")[0]
        ops[name] = (alone, comb)

    # --- figure ---
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.4))
    ax[0].plot(alphas, rho_a, "-o", ms=3, color="#2b6cb0")
    ax[0].axhline(spearmanr(T.retention, auc)[0], ls="--", color="#38a169", lw=0.9, label="retention only (α=1)")
    ax[0].axhline(spearmanr(T.effrank, auc)[0], ls="--", color="#d69e2e", lw=0.9, label="effrank only (α=0)")
    ax[0].axvline(0.5, ls=":", color="grey", lw=0.8); ax[0].scatter([0.5], [rho_a[10]], c="#c53030", zorder=5, label="used (α=0.5)")
    ax[0].set_xlabel("weight α on invariance   (Q = α·z(ret) + (1−α)·z(eff))")
    ax[0].set_ylabel("Spearman ρ vs downstream"); ax[0].set_ylim(0, 0.9)
    ax[0].set_title(f"Combination weight (best α≈{best_a:.2f}, plateau spans the middle)"); ax[0].legend(fontsize=8)

    names = list(ops); alone = [ops[n][0] for n in names]; comb = [ops[n][1] for n in names]
    x = np.arange(len(names)); w = 0.38
    ax[1].bar(x - w/2, alone, w, label="invariance alone", color="#38a169")
    ax[1].bar(x + w/2, comb, w, label="+ effrank (combined)", color="#2b6cb0")
    ax[1].set_xticks(x); ax[1].set_xticklabels(names, rotation=20, fontsize=8); ax[1].axhline(0, color="k", lw=0.5)
    ax[1].set_ylabel("Spearman ρ vs downstream"); ax[1].set_title("Invariance operationalization"); ax[1].legend(fontsize=8)
    fig.tight_layout(); p = os.path.join(FIGDIR, "sensitivity.png"); fig.savefig(p, dpi=150)

    print(f"[SAVED] {p} + results/sensitivity_alpha.csv\n")
    print("=== A. combination weight α (Q = α·z(retention)+(1−α)·z(effrank)) ===")
    for a in [0.0, 0.3, 0.4, 0.5, 0.6, 0.7, 1.0]:
        print(f"    α={a:.1f}  ρ={rho_a[int(round(a*20))]:+.3f}")
    lo = min(rho_a[6:15]); print(f"  plateau α∈[0.3,0.7]: ρ ≥ {lo:.3f}  (headline α=0.5 → {rho_a[10]:+.3f})")
    print("\n=== B. invariance operationalization (vision-only) ===")
    print("    measure        alone   +effrank")
    for n in names: print(f"    {n:13s}  {ops[n][0]:+.3f}   {ops[n][1]:+.3f}")


if __name__ == "__main__":
    run()
