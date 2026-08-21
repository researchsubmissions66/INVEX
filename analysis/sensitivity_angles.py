"""
Ablation #13: does the invariance signal need all three dihedral rotations, or is one enough?
Per-angle retention@10 (rot90 / rot180 / rot270 individually, pairs, all-three), each alone and
combined with effrank, correlated with the downstream oracle (vision-only). Instant (invariance CSVs).
Output: printed table + results/sensitivity_angles.csv
"""
import os, glob, itertools
import numpy as np, pandas as pd
from scipy.stats import spearmanr
from _common import load_metrics, vision_only, zscore
from config import OUT, VLM


def run():
    T = vision_only(load_metrics()); eff = T.effrank; auc = T.auc
    d16 = pd.concat([pd.read_csv(f) for f in glob.glob(os.path.join(OUT, "invariance_*.csv"))
                     if "summary" not in f], ignore_index=True)
    d16 = d16[~d16.encoder.isin(VLM)]

    def ret_over(transforms):
        return d16[d16["transform"].isin(transforms)].groupby("encoder")["retention@10"].mean().reindex(T.index)

    rots = ["rot90", "rot180", "rot270"]
    combos = ([("rot90",), ("rot180",), ("rot270",)] +
              list(itertools.combinations(rots, 2)) +
              [("rot90", "rot180", "rot270")])
    rows = []
    print("=== per-angle invariance ablation (vision-only) ===")
    print("   angles                 alone    +effrank")
    for c in combos:
        s = ret_over(list(c))
        alone = spearmanr(s, auc, nan_policy="omit")[0]
        comb = spearmanr(zscore(s) + zscore(eff), auc, nan_policy="omit")[0]
        name = "+".join(x.replace("rot", "") for x in c)
        rows.append({"angles": name, "rho_alone": alone, "rho_combined": comb})
        mark = "  <<< used" if len(c) == 3 else ""
        print(f"   {name:20s}  {alone:+.3f}    {comb:+.3f}{mark}")
    pd.DataFrame(rows).to_csv(os.path.join(OUT, "sensitivity_angles.csv"), index=False)
    print(f"\n[SAVED] results/sensitivity_angles.csv")


if __name__ == "__main__":
    run()
