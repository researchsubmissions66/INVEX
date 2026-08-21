"""Aggregate the Invariance invariance results: per-encoder rotation/stain invariance,
family breakdown, and how it relates to consensus + downstream (on the same 5 datasets)."""
import glob, os
import numpy as np, pandas as pd
from scipy.stats import spearmanr
from config import OUT, FAMILY

fs = glob.glob(os.path.join(OUT, "invariance_*.csv"))
d = pd.concat([pd.read_csv(f) for f in fs], ignore_index=True)
print(f"loaded {d.encoder.nunique()} encoders, {d.dataset.nunique()} datasets")

ROT = ["rot90", "rot180", "rot270"]
tr = d["transform"]  # avoid the DataFrame.transform method collision
# rotation invariance = mean over 3 rotations, averaged across datasets
rot = d[tr.isin(ROT)].groupby("encoder")[["retention@10","recall@1","ratio"]].mean()
hfl = d[tr=="hflip"].groupby("encoder")["retention@10"].mean().rename("hflip_ret")
stn = d[tr=="stain_hed"].groupby("encoder")["retention@10"].mean().rename("stain_ret")
T = rot.rename(columns={"retention@10":"rot_ret","recall@1":"rot_r1","ratio":"rot_ratio"}).join([hfl,stn])
T["family"] = [FAMILY.get(e,"?") for e in T.index]
T = T.sort_values("rot_ret", ascending=False)
T.to_csv(os.path.join(OUT,"invariance_summary.csv"))

print("\n=== ROTATION-INVARIANCE RANKING (all encoders) ===")
print(T[["family","rot_ret","rot_r1","rot_ratio","hflip_ret","stain_ret"]].round(3).to_string())

print("\n=== per-family mean rotation-invariance (retention) ===")
print(T.groupby("family").rot_ret.agg(["mean","std","count"]).round(3).to_string())

# relate to consensus + downstream; prefer 16-dataset means (linear_probe_oracle), else 5-dataset (money_plot)
p15 = os.path.join(OUT,"linear_probe_oracle_scores.csv"); p11 = os.path.join(OUT,"money_plot_encoder_summary.csv")
if os.path.exists(p15):
    s = pd.read_csv(p15).groupby("encoder")[["consensus","auc"]].mean().rename(
        columns={"consensus":"mean_consensus","auc":"mean_auc"}); src="linear_probe_oracle / 16 datasets"
elif os.path.exists(p11):
    s = pd.read_csv(p11).set_index("encoder"); src="money_plot / 5 datasets"
else:
    s = None
if s is not None:
    J = T.join(s[["mean_consensus","mean_auc"]], how="inner").dropna()
    print(f"\n=== rotation-invariance vs other metrics (oracle={src}, n={len(J)} encoders) ===")
    for x,y,lbl in [("rot_ret","mean_consensus","rotation-inv ~ consensus"),
                    ("rot_ret","mean_auc","rotation-inv ~ downstream-AUC"),
                    ("mean_consensus","mean_auc","consensus ~ downstream (ref)")]:
        r,p = spearmanr(J[x],J[y]); print(f"  {lbl:32s} rho={r:+.3f}  p={p:.3f}")
    J.to_csv(os.path.join(OUT,"invariance_vs_metrics.csv"))

# plot
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
col={"path_ssl":"#2b6cb0","path_vlm":"#d69e2e","path_other":"#718096","baseline":"#c53030"}
fig,ax=plt.subplots(figsize=(9,9))
ax.barh(range(len(T)), T.rot_ret, color=[col[f] for f in T.family], edgecolor="black", linewidth=.3)
ax.set_yticks(range(len(T))); ax.set_yticklabels(T.index, fontsize=8); ax.invert_yaxis()
ax.set_xlabel("rotation-invariance (retention@10, mean over rot90/180/270 & 5 datasets)")
ax.set_title("First-principles invariance metric: rotation-invariance by encoder")
from matplotlib.patches import Patch
ax.legend(handles=[Patch(color=c,label=l) for l,c in col.items()], fontsize=8)
plt.tight_layout(); plt.savefig(os.path.join(OUT,"plot_invariance.png"), dpi=140)
print("\n[SAVED] invariance_summary.csv + plot_invariance.png")
