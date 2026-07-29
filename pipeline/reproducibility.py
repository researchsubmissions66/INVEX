"""
Phase 15 — The reproducibility story on ALL 16 patch datasets, broken down by encoder family.

Per dataset (single native resolution): label-free Mutual-kNN CONSENSUS per encoder
+ PATIENT-GROUPED downstream AUC per encoder. Then:
  * Kendall W of CONSENSUS rankings across the 16 datasets   (label-free reproducibility)
  * Kendall W of DOWNSTREAM rankings across the 16 datasets  (benchmark reproducibility)
  * task-task Spearman (benchmark self-agreement) vs consensus-task Spearman (informativeness)
  * SAME, restricted WITHIN the dominant pathology-SSL family (rebuts "just family conformity")
  * per-family mean consensus (face validity) + leave-one-family-out ranking stability

Outputs: phase15_scores.csv, phase15_reproducibility.csv, plot_phase15_family.png
Resumable: appends per-dataset; stores each dataset's 28x28 agreement matrix for LOFO.
"""
import os, sys, time, glob, itertools
import numpy as np, pandas as pd, h5py
from scipy.stats import spearmanr
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold
import warnings; warnings.filterwarnings("ignore")
try:
    from sklearn.model_selection import StratifiedGroupKFold; HAS_SGK = True
except Exception:
    from sklearn.model_selection import GroupKFold; HAS_SGK = False
from utils import family as mf
from config import FEAT, META, OUT, DATASETS, FAMILY, EXCLUDE

SEED, K, FOLDS, CONS_N, PROBE_N = 42, 10, 5, 10000, 40000

rng = np.random.default_rng(SEED)
SCORES = os.path.join(OUT, "phase15_scores.csv")
AMAT = os.path.join(OUT, "phase15_amatrices.npz")

def encoders_for(ds):
    return [os.path.basename(p)[len("features_"):-3]
            for p in sorted(glob.glob(os.path.join(FEAT, ds, "features_*.h5")))
            if os.path.basename(p)[len("features_"):-3] not in EXCLUDE]

def strat_sub(y, cap):
    idx = np.arange(len(y))
    if len(y) <= cap: return idx
    keep = [rng.choice(idx[y==c], min(len(idx[y==c]), max(1, cap*len(idx[y==c])//len(y))),
                       replace=False) for c in np.unique(y)]
    return np.sort(np.concatenate(keep))

def probe_auc(X, y, groups, folds=FOLDS):
    classes = np.unique(y); mc = len(classes) > 2
    use_g = groups is not None and len(np.unique(groups)) >= folds
    if use_g and HAS_SGK:
        sp = StratifiedGroupKFold(folds, shuffle=True, random_state=SEED).split(X, y, groups); mode="grouped"
    elif use_g:
        sp = GroupKFold(folds).split(X, y, groups); mode="grouped"
    else:
        sp = StratifiedKFold(folds, shuffle=True, random_state=SEED).split(X, y); mode="patch"
    aucs = []
    for tr, te in sp:
        sc = StandardScaler().fit(X[tr])
        clf = LogisticRegression(max_iter=500, n_jobs=-1, multi_class="ovr" if mc else "auto").fit(sc.transform(X[tr]), y[tr])
        if len(np.unique(y[te])) < 2: continue
        pr = clf.predict_proba(sc.transform(X[te]))
        if mc:
            if len(clf.classes_) != len(classes): continue
            aucs.append(roc_auc_score(y[te], pr, multi_class="ovr", labels=clf.classes_))
        else:
            aucs.append(roc_auc_score(y[te], pr[:, 1]))
    return (float(np.mean(aucs)) if aucs else np.nan), mode

# ---------- compute per dataset (resumable) ----------
done = set()
if os.path.exists(SCORES):
    done = set(pd.read_csv(SCORES).dataset.unique())
amats = dict(np.load(AMAT)) if os.path.exists(AMAT) else {}

for ds in DATASETS:
    if ds in done:
        print(f"[skip] {ds} already computed"); continue
    t0 = time.time()
    encs = encoders_for(ds)
    df = pd.read_csv(os.path.join(META, ds, "metadata.csv")).reset_index(drop=True)
    y_all = LabelEncoder().fit_transform(df["label"].astype(str).values)
    pid = df["patient_id"].astype(str).str.strip().replace({"nan": ""}).values
    has_pid = (pid != "").all() and len(set(pid)) > 1
    probe_idx = strat_sub(y_all, PROBE_N)
    cons_idx = probe_idx if len(probe_idx) <= CONS_N else np.sort(rng.choice(probe_idx, CONS_N, replace=False))
    print(f"\n=== {ds}: {len(encs)} enc, N={len(df)}, probe={len(probe_idx)}, cons={len(cons_idx)}, "
          f"patients={'yes' if has_pid else 'NO'} ===", flush=True)

    fc, fp = {}, {}
    for e in encs:
        with h5py.File(os.path.join(FEAT, ds, f"features_{e}.h5"), "r") as f:
            if f["features"].shape[0] != len(df): continue
            F = f["features"][:]
        fc[e] = F[cons_idx]; fp[e] = F[probe_idx].astype("float32"); del F
    encs = list(fp)
    knn = {e: mf.build_knn(fc[e], K) for e in encs}
    A, order = mf.mutual_knn_matrix(knn, K)
    cons = mf.mean_consensus(A)
    amats[ds] = pd.DataFrame(A, index=order, columns=order).to_json()

    yg = y_all[probe_idx]; gg = pid[probe_idx] if has_pid else None
    rows = []
    for i, e in enumerate(order):
        auc, mode = probe_auc(fp[e], yg, gg)
        rows.append({"dataset": ds, "encoder": e, "family": FAMILY.get(e, "?"),
                     "consensus": float(cons[i]), "auc": auc, "cv": mode})
        print(f"  {e:15s} [{FAMILY.get(e,'?'):9s}] cons={cons[i]:.3f} auc={auc:.3f}", flush=True)
    pd.DataFrame(rows).to_csv(SCORES, mode="a", header=not os.path.exists(SCORES), index=False)
    np.savez(AMAT, **amats)
    print(f"  {ds} done in {time.time()-t0:.0f}s", flush=True)

# ---------- reproducibility analysis ----------
S = pd.read_csv(SCORES)
CON = S.pivot(index="encoder", columns="dataset", values="consensus")
AUC = S.pivot(index="encoder", columns="dataset", values="auc")
common = CON.dropna().index.intersection(AUC.dropna().index)
CON, AUC = CON.loc[common], AUC.loc[common]
fam = {e: FAMILY.get(e, "?") for e in common}

def kendall_w(mat):
    R = mat.rank(axis=0); n, m = R.shape; Rj = R.sum(1)
    return float(12*((Rj-Rj.mean())**2).sum()/(m**2*(n**3-n)))

def pair_spear(mat):
    cs = mat.columns; v = [spearmanr(mat[a], mat[b])[0] for a, b in itertools.combinations(cs, 2)]
    return float(np.mean(v))

def cons_vs_task(con, auc):
    return float(np.mean([spearmanr(con[t], auc[t])[0] for t in auc.columns]))

def block(idx, label):
    c, a = CON.loc[idx], AUC.loc[idx]
    return {"scope": label, "n_encoders": len(idx),
            "consensus_W": kendall_w(c), "downstream_W": kendall_w(a),
            "task_task_rho": pair_spear(a), "consensus_task_rho": cons_vs_task(c, a)}

res = [block(common, f"ALL ({len(common)} enc, {CON.shape[1]} datasets)")]
for f in ["path_ssl", "path_vlm", "baseline"]:
    idx = [e for e in common if fam[e] == f]
    if len(idx) >= 4:
        res.append(block(idx, f"family={f}"))
rep = pd.DataFrame(res)
rep.to_csv(os.path.join(OUT, "phase15_reproducibility.csv"), index=False)

# leave-one-family-out: recompute consensus excluding a family's votes, measure rank stability
lofo = []
for f in ["path_ssl", "path_vlm", "baseline"]:
    stab = []
    for ds in CON.columns:
        Aj = pd.read_json(amats[ds]); keep = [e for e in Aj.columns if fam.get(e) != f]
        full = Aj.loc[common].mean(axis=1)  # approx full-pool
        loo = Aj.loc[common, [k for k in keep if k in Aj.columns]].mean(axis=1)
        stab.append(spearmanr(full, loo)[0])
    lofo.append({"left_out_family": f, "mean_rank_stability_rho": float(np.mean(stab))})
pd.DataFrame(lofo).to_csv(os.path.join(OUT, "phase15_lofo.csv"), index=False)

# per-family mean consensus (face validity)
famcons = S.groupby("family").consensus.agg(["mean", "std", "count"]).round(3)

print("\n" + "="*70)
print("REPRODUCIBILITY (Kendall W: 1=identical rankings across datasets):")
print(rep.to_string(index=False, float_format=lambda x: f"{x:.3f}"))
print("\nLEAVE-ONE-FAMILY-OUT ranking stability (does the ranking survive dropping a family's votes?):")
print(pd.DataFrame(lofo).to_string(index=False, float_format=lambda x: f"{x:.3f}"))
print("\nPER-FAMILY mean consensus (face validity):")
print(famcons.to_string())

# ---------- plot ----------
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
mc = S.groupby("encoder").consensus.mean().sort_values(ascending=False)
colors = {"path_ssl":"#2b6cb0","path_vlm":"#d69e2e","path_other":"#718096","baseline":"#c53030"}
fig, ax = plt.subplots(1, 2, figsize=(17, 7), gridspec_kw={"width_ratios":[2,1]})
ax[0].barh(range(len(mc)), mc.values,
           color=[colors[FAMILY[e]] for e in mc.index], edgecolor="black", linewidth=0.3)
ax[0].set_yticks(range(len(mc))); ax[0].set_yticklabels(mc.index, fontsize=8); ax[0].invert_yaxis()
ax[0].set_xlabel("mean Mutual-kNN consensus (16 datasets)")
ax[0].set_title("Label-free ranking, colored by family")
from matplotlib.patches import Patch
ax[0].legend(handles=[Patch(color=c, label=l) for l, c in colors.items()], fontsize=8)
rr = rep.set_index("scope")
labels = list(rr.index); x = np.arange(len(labels)); w = 0.35
ax[1].bar(x-w/2, rr.consensus_W, w, label="consensus W", color="#2b6cb0")
ax[1].bar(x+w/2, rr.downstream_W, w, label="downstream W", color="#c53030")
ax[1].set_xticks(x); ax[1].set_xticklabels([l.split("(")[0].split("=")[-1] for l in labels], rotation=30, fontsize=8)
ax[1].set_ylabel("Kendall W"); ax[1].set_title("Reproducibility: label-free vs benchmarks"); ax[1].legend(fontsize=8)
plt.tight_layout(); plt.savefig(os.path.join(OUT, "plot_phase15_family.png"), dpi=140)
print("\n[SAVED] plot_phase15_family.png + phase15_reproducibility.csv + phase15_lofo.csv")
