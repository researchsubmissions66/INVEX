"""
KNN — KNN probing as a second downstream oracle (CPU).

A non-parametric alternative to the linear probe: classify each patch by majority vote of its
k nearest neighbours (cosine) among the training patches, scored by macro AUC under the SAME
patient-grouped cross-validation. Gives a per-encoder downstream number that does not depend on a
linear classifier, so we can test whether our label-free metric predicts quality regardless of how
quality is measured.

Outputs: knn_probe_oracle_scores.csv (dataset, encoder, knn_auc, cv), and a quick comparison of the KNN
oracle vs the linear-probe oracle (Linear Probe Oracle) and vs rotation-invariance (Invariance).
"""
import os, sys, glob, time
import numpy as np, pandas as pd, h5py
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold
from scipy.stats import spearmanr
import warnings; warnings.filterwarnings("ignore")
try:
    from sklearn.model_selection import StratifiedGroupKFold; HAS_SGK = True
except Exception:
    from sklearn.model_selection import GroupKFold; HAS_SGK = False

from config import FEAT, META, OUT, DATASETS, EXCLUDE
K, FOLDS, CAP, SEED = 20, 5, 20000, 42
rng = np.random.default_rng(SEED)

def strat_sub(y, cap):
    idx = np.arange(len(y))
    if len(y) <= cap: return idx
    keep = [rng.choice(idx[y==c], min(len(idx[y==c]), max(1, cap*len(idx[y==c])//len(y))), replace=False)
            for c in np.unique(y)]
    return np.sort(np.concatenate(keep))

def knn_auc(X, y, groups):
    classes = np.unique(y); mc = len(classes) > 2
    Xn = X / (np.linalg.norm(X, axis=1, keepdims=True) + 1e-9)   # cosine == dot on normalized
    use_g = groups is not None and len(np.unique(groups)) >= FOLDS
    if use_g and HAS_SGK:
        sp = StratifiedGroupKFold(FOLDS, shuffle=True, random_state=SEED).split(Xn, y, groups); mode="grouped"
    elif use_g:
        sp = GroupKFold(FOLDS).split(Xn, y, groups); mode="grouped"
    else:
        sp = StratifiedKFold(FOLDS, shuffle=True, random_state=SEED).split(Xn, y); mode="patch"
    aucs = []
    for tr, te in sp:
        if len(np.unique(y[te])) < 2: continue
        clf = KNeighborsClassifier(n_neighbors=K, metric="cosine", algorithm="brute", n_jobs=-1).fit(Xn[tr], y[tr])
        pr = clf.predict_proba(Xn[te])
        if mc:
            if pr.shape[1] != len(classes): continue
            aucs.append(roc_auc_score(y[te], pr, multi_class="ovr", labels=clf.classes_))
        else:
            aucs.append(roc_auc_score(y[te], pr[:, 1]))
    return (float(np.mean(aucs)) if aucs else np.nan), mode

def encoders_for(ds):
    return [os.path.basename(p)[len("features_"):-3] for p in sorted(glob.glob(os.path.join(FEAT, ds, "features_*.h5")))
            if os.path.basename(p)[len("features_"):-3] not in EXCLUDE]

t0 = time.time(); rows = []
for ds in DATASETS:
    df = pd.read_csv(os.path.join(META, ds, "metadata.csv")).reset_index(drop=True)
    y = LabelEncoder().fit_transform(df["label"].astype(str).values)
    pid = df["patient_id"].astype(str).str.strip().replace({"nan": ""}).values
    has_pid = (pid != "").all() and len(set(pid)) > 1
    idx = strat_sub(y, CAP)
    yg = y[idx]; gg = pid[idx] if has_pid else None
    print(f"\n=== {ds}: N={len(df)} sub={len(idx)} patients={'yes' if has_pid else 'NO'} ===", flush=True)
    for e in encoders_for(ds):
        with h5py.File(os.path.join(FEAT, ds, f"features_{e}.h5"), "r") as f:
            if f["features"].shape[0] != len(df): continue
            X = f["features"][:][idx].astype("float32")
        auc, mode = knn_auc(X, yg, gg)
        rows.append({"dataset": ds, "encoder": e, "knn_auc": auc, "cv": mode})
        print(f"  {e:15s} knn_auc={auc:.4f} [{mode}]", flush=True)

kdf = pd.DataFrame(rows); kdf.to_csv(os.path.join(OUT, "knn_probe_oracle_scores.csv"), index=False)
knn = kdf.groupby("encoder").knn_auc.mean()
print(f"\n[SAVED] knn_probe_oracle_scores.csv  ({time.time()-t0:.0f}s)")

# ---- compare KNN oracle to linear-probe oracle + rotation metric ----
lin = pd.read_csv(os.path.join(OUT, "linear_probe_oracle_scores.csv")).groupby("encoder").auc.mean()
d = pd.concat([pd.read_csv(f) for f in glob.glob(os.path.join(OUT, "invariance_*.csv"))], ignore_index=True)
ret = d[d["transform"].isin(["rot90","rot180","rot270"])].groupby("encoder")["retention@10"].mean()
J = pd.DataFrame({"knn_probe_oracle": knn, "lin": lin, "ret": ret}).dropna()
print(f"\n=== KNN oracle vs linear-probe oracle (n={len(J)} encoders) ===")
print(f"  agreement of the two oracles     Spearman={spearmanr(J.knn, J.lin)[0]:+.3f}")
print(f"  rotation-invariance ~ KNN oracle Spearman={spearmanr(J.ret, J.knn)[0]:+.3f}")
print(f"  rotation-invariance ~ lin oracle Spearman={spearmanr(J.ret, J.lin)[0]:+.3f}")
