"""
Probabilistic — Probabilistic / Bayesian upgrade of the rotation-invariance metric (CPU).

Idea: embeddings live on the unit sphere, so model directions with von Mises-Fisher (vMF).
Two concentrations capture the two halves of quality:
  * INVARIANCE   kappa_nuis : how tightly rotated views cluster around their clean originals.
                 mean cosine R_nuis = 1 - align_dist  ->  kappa via Banerjee MLE.
  * EXPRESSIVENESS 1/kappa_bio : how DIFFUSE the whole cloud is (spread = discriminative).
                 mean cosine R_bio = 1 - bio_spread   ->  kappa_bio.
Quality likelihood-ratio:  Q_vmf = log kappa_nuis - log kappa_bio   (invariant within nuisance,
spread across biology). Adds the discriminability term the retention metric was missing; the
dimension d ~cancels in the ratio, so it is not d-confounded like raw effective rank.

Also compute expressiveness directly from cached clean embeddings (effective rank, -uniformity)
and test invariance+expressiveness combinations. Bayesian layer: Dirichlet (Bayesian-bootstrap)
posteriors over the 16 datasets for per-encoder credible intervals, and bootstrap CIs on the
downstream Spearman. Head-to-head vs the current retention@10.

Outputs: probabilistic_prob_scores.csv, probabilistic_leaderboard.csv, plot_probabilistic.png
"""
import os, glob, sys
import numpy as np, pandas as pd, h5py
from scipy.stats import spearmanr
from utils import intrinsic as im
from config import FEAT, OUT, FAMILY as FAM, VLM
ROT  = ["rot90", "rot180", "rot270"]
SUB  = 3000                      # subsample for effrank/uniformity
rng  = np.random.default_rng(0)

from utils.intrinsic import kappa

def dim_of(enc):
    for ds in ["MHIST", "CHAOYANG", "Kather-MSI-CRC"]:
        p = os.path.join(FEAT, ds, f"features_{enc}.h5")
        if os.path.exists(p):
            with h5py.File(p, "r") as f:
                return f["features"].shape[1]
    return np.nan

def expressiveness(enc, datasets):
    """effective rank & uniformity on cached clean embeddings (subsample), mean over datasets."""
    ers, unis = [], []
    for ds in datasets:
        p = os.path.join(FEAT, ds, f"features_{enc}.h5")
        if not os.path.exists(p): continue
        with h5py.File(p, "r") as f:
            n = f["features"].shape[0]
            idx = np.sort(rng.choice(n, min(SUB, n), replace=False))
            Z = f["features"][:][idx].astype("float32")
        ers.append(im.effective_rank(Z)); unis.append(im.uniformity(Z))
    return (np.mean(ers) if ers else np.nan), (np.mean(unis) if unis else np.nan)

# ---------- assemble per-encoder, per-dataset table ----------
d = pd.concat([pd.read_csv(f) for f in glob.glob(os.path.join(OUT, "invariance_*.csv"))],
              ignore_index=True)
_agg = dict(align=("align_dist","mean"), spread=("bio_spread","mean"), retention=("retention@10","mean"))
HAS_SJS = "soft_js" in d.columns
if HAS_SJS: _agg["soft_js"] = ("soft_js", "mean")
rot = d[d["transform"].isin(ROT)].groupby(["encoder","dataset"]).agg(**_agg).reset_index()
dims = {e: dim_of(e) for e in rot.encoder.unique()}
rot["d"]     = rot["encoder"].map(dims)
rot["Rnuis"] = 1 - rot["align"]        # 'align' is a DataFrame method -> must use bracket access
rot["Rbio"]  = 1 - rot["spread"]
rot["logk_nuis"] = np.log(kappa(rot["Rnuis"], rot["d"]))
rot["logk_bio"]  = np.log(kappa(rot["Rbio"],  rot["d"]))
rot["Q_vmf"]     = rot["logk_nuis"] - rot["logk_bio"]    # the likelihood-ratio quality
rot.to_csv(os.path.join(OUT, "probabilistic_prob_scores.csv"), index=False)

datasets = sorted(rot.dataset.unique())
_pagg = dict(retention=("retention","mean"), inv_kappa=("logk_nuis","mean"),
             exp_kbio=("logk_bio","mean"), Q_vmf=("Q_vmf","mean"))
if HAS_SJS: _pagg["soft_js"] = ("soft_js", "mean")
per = rot.groupby("encoder").agg(**_pagg).reset_index()
per["exp_kbio"] = -per.exp_kbio                          # orient: higher = more diffuse = expressive
# richer expressiveness from clean embeddings
er, un = zip(*[expressiveness(e, datasets) for e in per.encoder])
per["exp_effrank"] = er
per["exp_neg_unif"] = -np.array(un)
per["fam"] = per.encoder.map(FAM)

# ---------- combinations (invariance x expressiveness) ----------
z = lambda s: (s - s.mean()) / (s.std() + 1e-9)
per["Q_ret_effrank"] = z(per["retention"]) + z(per["exp_effrank"])
per["Q_ret_kbio"]    = z(per["retention"]) + z(per["exp_kbio"])
per["Q_ret_unif"]    = z(per["retention"]) + z(per["exp_neg_unif"])
if HAS_SJS:
    per["Q_sjs_effrank"] = z(per["soft_js"]) + z(per["exp_effrank"])

# ---------- oracle + validation ----------
auc = pd.read_csv(os.path.join(OUT, "linear_probe_oracle_scores.csv")).groupby("encoder").auc.mean()
J = per.set_index("encoder").join(auc.rename("auc")).dropna(subset=["auc"])

def boot_ci(x, y, B=10000):
    n = len(x); o = []
    for _ in range(B):
        b = rng.integers(0, n, n)
        if len(np.unique(x[b])) > 2: o.append(spearmanr(x[b], y[b])[0])
    return np.percentile(o, [2.5, 50, 97.5])

METRICS = ["retention","inv_kappa","exp_kbio","exp_effrank","exp_neg_unif",
           "Q_vmf","Q_ret_effrank","Q_ret_kbio","Q_ret_unif"]
KIND = {"retention":"invariance(old)","inv_kappa":"invariance(vMF)","exp_kbio":"express(vMF)",
        "exp_effrank":"express(rank)","exp_neg_unif":"express(unif)","Q_vmf":"COMBINED(vMF ratio)",
        "Q_ret_effrank":"COMBINED(ret+rank)","Q_ret_kbio":"COMBINED(ret+kbio)","Q_ret_unif":"COMBINED(ret+unif)"}
if HAS_SJS:
    METRICS += ["soft_js", "Q_sjs_effrank"]
    KIND["soft_js"] = "invariance(soft-JS)"; KIND["Q_sjs_effrank"] = "COMBINED(softJS+rank)"
rows = []
for subset, idx in [("all", J.index),
                    ("vision-only", J.index[~J.index.isin(VLM)]),
                    ("SSL+other", J.index[J.fam.isin(["path_ssl","path_other"])]),
                    ("path_ssl(DINOv2-family)", J.index[J.fam=="path_ssl"])]:
    Y = J.loc[idx, "auc"].values
    for m in METRICS:
        X = J.loc[idx, m].values
        ok = np.isfinite(X)
        rho, _ = spearmanr(X[ok], Y[ok]); lo, md, hi = boot_ci(X[ok], Y[ok])
        rows.append({"subset":subset,"metric":m,"kind":KIND[m],"n":ok.sum(),
                     "rho":rho,"ci_lo":lo,"ci_hi":hi})
lb = pd.DataFrame(rows)
lb.to_csv(os.path.join(OUT, "probabilistic_leaderboard.csv"), index=False)

for subset in ["all","vision-only","SSL+other","path_ssl(DINOv2-family)"]:
    s = lb[lb.subset==subset].sort_values("rho", ascending=False)
    print(f"\n=== {subset} (n={s.n.iloc[0]}) — rho vs downstream, best first ===")
    for _, r in s.iterrows():
        star = "  <<<" if r.metric=="retention" else ("  *" if r.kind.startswith("COMB") else "")
        print(f"  {r['kind']:22s} {r['metric']:16s} rho={r['rho']:+.3f}  CI[{r['ci_lo']:+.2f},{r['ci_hi']:+.2f}]{star}")

# ---------- plot: best combined vs retention, per subset ----------
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
best = lb[lb.kind.str.startswith("COMB")].loc[lb[lb.kind.str.startswith("COMB")].groupby("subset").rho.idxmax()]
fig, ax = plt.subplots(figsize=(8,5))
sub = ["all","vision-only","SSL+other","path_ssl(DINOv2-family)"]; x=np.arange(len(sub)); w=0.35
ret = [lb[(lb.subset==s)&(lb.metric=="retention")].rho.iloc[0] for s in sub]
bst = [best[best.subset==s].rho.iloc[0] for s in sub]
ax.bar(x-w/2, ret, w, label="retention@10 (current)", color="#718096")
ax.bar(x+w/2, bst, w, label="best probabilistic combo", color="#2b6cb0")
ax.set_xticks(x); ax.set_xticklabels(sub); ax.set_ylabel("Spearman rho vs downstream")
ax.axhline(0, color="k", lw=.5); ax.legend(); ax.set_title("Probabilistic: does invariance x expressiveness beat invariance alone?")
plt.tight_layout(); plt.savefig(os.path.join(OUT,"plot_probabilistic.png"), dpi=140)
print("\n[SAVED] probabilistic_leaderboard.csv + plot_probabilistic.png")
