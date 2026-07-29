"""
Top-k recovery + rank-regret: reframe rho=0.76 as a decision-useful shortlisting claim.

Practitioner setup: you can afford to run the *labeled* oracle on only k of N encoders. You use the
FREE score to pick the shortlist of k, then take the best of those. Two questions:
  * top-k recovery: how many of the truly-best-k does the free shortlist contain?
  * rank-regret(k): global-best AUC minus the best AUC inside the metric's top-k shortlist
                    (how much downstream you leave on the table by trusting the free score).
Compared against a random-shortlist baseline (expected regret) and the oracle-of-oracle (regret 0).
Outputs: figures/topk_regret.png, results/topk_regret.csv, printed headline sentences.
"""
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from _common import load_metrics, vision_only, FIGDIR
from config import OUT
import os


def topk_recovery(score, auc, k):
    top_m = set(score.sort_values(ascending=False).index[:k])
    top_a = set(auc.sort_values(ascending=False).index[:k])
    return len(top_m & top_a) / k


def regret_curve(score, auc):
    """regret(k) = best AUC overall - best AUC among the metric's top-k shortlist."""
    best = auc.max(); order = score.sort_values(ascending=False).index
    return np.array([best - auc.loc[order[:k]].max() for k in range(1, len(order) + 1)])


def random_regret(auc, reps=20000, seed=0):
    """expected regret of a random size-k shortlist (baseline)."""
    rng = np.random.default_rng(seed); a = auc.values; best = a.max(); N = len(a)
    out = np.zeros(N)
    for k in range(1, N + 1):
        out[k - 1] = np.mean([best - a[rng.choice(N, k, replace=False)].max() for _ in range(reps // 4)])
    return out


def run():
    T = load_metrics(); vo = vision_only(T)
    metrics = {"combined (invariance×discriminability)": "combined",
               "rotation invariance": "retention", "discriminability (effrank)": "effrank"}
    N = len(vo); ks = np.arange(1, N + 1)
    rand = random_regret(vo.auc)

    # --- figure: regret curves + top-k recovery ---
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.4))
    rows = []
    colors = {"combined": "#2b6cb0", "retention": "#38a169", "effrank": "#d69e2e"}
    for name, col in metrics.items():
        reg = regret_curve(vo[col], vo.auc)
        rec = [topk_recovery(vo[col], vo.auc, k) for k in ks]
        ax[0].plot(ks, reg, "-o", ms=3, color=colors[col], label=name)
        ax[1].plot(ks, rec, "-o", ms=3, color=colors[col], label=name)
        for k in ks:
            rows.append({"metric": col, "k": int(k), "regret_auc": regret_curve(vo[col], vo.auc)[k-1],
                         "topk_recovery": topk_recovery(vo[col], vo.auc, k)})
    ax[0].plot(ks, rand, "--", color="grey", label="random shortlist")
    ax[0].set_xlabel("shortlist size k"); ax[0].set_ylabel("rank-regret (AUC left on the table)")
    ax[0].set_title(f"Rank-regret: free shortlist then oracle-test k of {N}"); ax[0].legend(fontsize=8)
    ax[0].axhline(0, color="k", lw=.5)
    ax[1].plot(ks, ks / N, "--", color="grey", label="random (=k/N)")
    ax[1].set_xlabel("shortlist size k"); ax[1].set_ylabel("top-k recovery (fraction of true best-k)")
    ax[1].set_title("Top-k recovery, vision-only (n=%d)" % N); ax[1].legend(fontsize=8)
    fig.tight_layout(); p = os.path.join(FIGDIR, "topk_regret.png"); fig.savefig(p, dpi=150)
    pd.DataFrame(rows).to_csv(os.path.join(OUT, "topk_regret.csv"), index=False)

    # --- headline sentences ---
    c = vo["combined"]
    true3 = set(vo.auc.sort_values(ascending=False).index[:3])
    m3 = list(c.sort_values(ascending=False).index[:3])
    hit3 = len(set(m3) & true3)
    reg1 = vo.auc.max() - vo.auc.loc[c.idxmax()]
    reg3 = vo.auc.max() - vo.auc.loc[c.sort_values(ascending=False).index[:3]].max()
    print(f"[SAVED] {p} + results/topk_regret.csv\n")
    print("=== HEADLINE (vision-only, combined metric) ===")
    print(f"  * The metric's top-3 contains {hit3} of the 3 truly-best encoders ({m3}).")
    print(f"  * Trusting the metric's #1 pick costs {reg1:.3f} AUC vs the true best (simple regret).")
    print(f"  * Shortlisting the metric's top-3 and oracle-testing only those recovers to within "
          f"{reg3:.3f} AUC of the global best (vs a full {N}-encoder sweep).")
    print(f"  * A random top-3 shortlist would leave {rand[2]:.3f} AUC on the table "
          f"({rand[2]/max(reg3,1e-9):.1f}x worse than the metric).")


if __name__ == "__main__":
    run()
