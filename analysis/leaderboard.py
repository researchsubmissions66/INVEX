"""
Predicted-vs-actual leaderboard: two ranked columns (label-free metric rank <-> oracle rank) with
connecting lines. Short, near-horizontal lines = good agreement; long crossing lines = disagreement
(these are the informative cases to discuss, e.g. uni_v2). Vision-only roster.
Outputs: figures/leaderboard.png, results/leaderboard.csv
"""
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from scipy.stats import spearmanr, kendalltau
from _common import load_metrics, vision_only, FIGDIR, FAM_COLOR
from config import OUT
import os


def run():
    T = vision_only(load_metrics()); N = len(T)
    m_rank = T["combined"].rank(ascending=False).astype(int)
    a_rank = T["auc"].rank(ascending=False).astype(int)
    lb = pd.DataFrame({"metric_rank": m_rank, "oracle_rank": a_rank,
                       "combined": T["combined"], "auc": T["auc"], "family": T["family"]}
                      ).sort_values("oracle_rank")
    lb.to_csv(os.path.join(OUT, "leaderboard.csv"))
    rho = spearmanr(T["combined"], T["auc"])[0]; tau = kendalltau(T["combined"], T["auc"])[0]

    fig, ax = plt.subplots(figsize=(6.6, 8)); yL, yR = 0.0, 0.0
    posL = {e: N - m_rank[e] for e in T.index}          # metric column (left)
    posR = {e: N - a_rank[e] for e in T.index}          # oracle column (right)
    for e in T.index:
        ax.plot([0, 1], [posL[e], posR[e]], "-", color=FAM_COLOR[T.loc[e, "family"]], alpha=0.6, lw=1.3)
        ax.text(-0.02, posL[e], f"{m_rank[e]:>2}. {e}", ha="right", va="center", fontsize=7.5)
        ax.text(1.02, posR[e], f"{e} .{a_rank[e]:<2}", ha="left", va="center", fontsize=7.5)
    ax.text(0, N + 0.6, "label-free metric", ha="center", fontweight="bold", fontsize=10)
    ax.text(1, N + 0.6, "downstream oracle", ha="center", fontweight="bold", fontsize=10)
    ax.set_xlim(-0.55, 1.55); ax.set_ylim(-1, N + 1.5); ax.axis("off")
    ax.set_title(f"Predicted vs actual encoder ranking (vision-only, n={N})\n"
                 f"Spearman ρ={rho:.2f}   Kendall τ={tau:.2f}", fontsize=11)
    fig.tight_layout(); p = os.path.join(FIGDIR, "leaderboard.png"); fig.savefig(p, dpi=150)
    print(f"[SAVED] {p} + results/leaderboard.csv   (ρ={rho:.3f}, τ={tau:.3f})")


if __name__ == "__main__":
    run()
