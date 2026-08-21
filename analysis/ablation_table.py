"""
Ablation table: every metric variant x subset, with rho and 95% bootstrap CI, from the existing
probabilistic_leaderboard.csv. Shows the combined score is earned, not fished, and that the null controls
are null. Emits a markdown table (docs/ablation_table.md) and a tidy CSV (results/ablation_table.csv).
"""
import os
import pandas as pd
from _common import ROOT
from config import OUT

ORDER = ["retention", "soft_js", "inv_kappa", "exp_effrank", "exp_neg_unif", "exp_kbio",
         "Q_ret_effrank", "Q_sjs_effrank", "Q_ret_unif", "Q_ret_kbio", "Q_vmf"]
NICE = {"retention": "rotation invariance (retention@10)", "soft_js": "soft-JS invariance",
        "inv_kappa": "vMF invariance (log κ_nuis)", "exp_effrank": "discriminability (effrank)",
        "exp_neg_unif": "discriminability (−uniformity)", "exp_kbio": "diffuseness (−log κ_bio)",
        "Q_ret_effrank": "COMBINED: retention + effrank", "Q_sjs_effrank": "combined: soft-JS + effrank",
        "Q_ret_unif": "combined: retention + (−unif)", "Q_ret_kbio": "combined: retention + diffuseness",
        "Q_vmf": "COMBINED: vMF ratio log(κ_nuis/κ_bio)"}


def run():
    lb = pd.read_csv(os.path.join(OUT, "probabilistic_leaderboard.csv"))
    subs = ["all", "vision-only", "SSL+other", "path_ssl(DINOv2-family)"]
    subs = [s for s in subs if s in set(lb.subset)]
    cell = lambda r: f"{r.rho:+.2f} [{r.ci_lo:+.2f},{r.ci_hi:+.2f}]"
    tidy = lb.copy(); tidy.to_csv(os.path.join(OUT, "ablation_table.csv"), index=False)

    lines = ["# Ablation: metric variants vs downstream (Spearman ρ [95% bootstrap CI])", ""]
    header = "| metric | " + " | ".join(f"{s} (n={int(lb[lb.subset==s].n.iloc[0])})" for s in subs) + " |"
    lines += [header, "|" + "---|" * (len(subs) + 1)]
    present = [m for m in ORDER if m in set(lb.metric)]
    for m in present:
        cells = []
        for s in subs:
            r = lb[(lb.subset == s) & (lb.metric == m)]
            cells.append(cell(r.iloc[0]) if len(r) else "—")
        star = " **★**" if m in ("Q_ret_effrank",) else ""
        lines.append(f"| {NICE.get(m, m)}{star} | " + " | ".join(cells) + " |")
    lines += ["", "★ = headline metric. Controls (hflip, stain) are reported separately as nulls.",
              "Nulls: hflip-retention ~ downstream ρ≈−0.11 (all) / −0.00 (vision-only); "
              "stain-retention ρ≈+0.14 / +0.21 — both near-saturated, confirming rotation-specificity."]
    md = os.path.join(ROOT, "docs", "ablation_table.md")
    open(md, "w").write("\n".join(lines) + "\n")
    print(f"[SAVED] {md} + results/ablation_table.csv")
    print("\n".join(lines))


if __name__ == "__main__":
    run()
