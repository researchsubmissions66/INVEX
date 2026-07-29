"""
Hero figure: the two-axis thesis in one plot.
x = rotation invariance (retention@10), y = discriminability (effective rank),
color = downstream AUC, marker = family. The named counterexample (uni_v2: top AUC, mid
invariance) is annotated so we surface it rather than hide it.
Output: figures/hero_scatter.png
"""
import numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from _common import load_metrics, FIGDIR, FAM_COLOR, FAM_MARKER, FAM_LABEL
import os


def run():
    T = load_metrics()
    fig, ax = plt.subplots(figsize=(8.4, 6.2))
    sc = None
    for fam, g in T.groupby("family"):
        sc = ax.scatter(g.retention, g.effrank, c=g.auc, s=120, marker=FAM_MARKER[fam],
                        cmap="viridis", edgecolor="black", linewidth=0.5, vmin=T.auc.min(), vmax=T.auc.max())
    for e, r in T.iterrows():
        ax.annotate(e, (r.retention, r.effrank), fontsize=6.5, xytext=(3, 3),
                    textcoords="offset points", alpha=0.8)
    # highlight the honest counterexample if present
    if "uni_v2" in T.index:
        u = T.loc["uni_v2"]
        ax.annotate("counterexample\n(top AUC, mid invariance)", (u.retention, u.effrank),
                    fontsize=7.5, xytext=(-90, -28), textcoords="offset points", color="#c53030",
                    arrowprops=dict(arrowstyle="->", color="#c53030", lw=1))
    cb = fig.colorbar(sc, ax=ax); cb.set_label("downstream AUC (oracle)")
    ax.set_xlabel("rotation invariance  (retention@10)")
    ax.set_ylabel("discriminability  (effective rank)")
    ax.set_title("INVEX: quality ≈ invariance × discriminability")
    handles = [Line2D([0], [0], marker=FAM_MARKER[f], color="w", markerfacecolor="grey",
                      markeredgecolor="k", markersize=9, label=FAM_LABEL[f]) for f in FAM_MARKER]
    ax.legend(handles=handles, fontsize=8, loc="lower right")
    fig.tight_layout(); p = os.path.join(FIGDIR, "hero_scatter.png"); fig.savefig(p, dpi=150)
    print(f"[SAVED] {p}")


if __name__ == "__main__":
    run()
