"""
Phase 11 — The Money Plot: does label-free Mutual-kNN Consensus predict
downstream quality?

For each hard dataset {MHIST, CHAOYANG, Kather-MSI-CRC, Kather-MSI-STAD, TCGA-TILs}:
  * CONSENSUS (label-free): per encoder, L2-normalize features, build k-NN graph
    (cosine), score = mean mutual-kNN overlap with all OTHER encoders in the pool.
    (This is the exact Platonic Consensus of Phase 5, recomputed per dataset.)
  * DOWNSTREAM (labels, oracle): per encoder, PATIENT-GROUPED 5-fold CV logistic
    regression -> macro AUC. Groups = patient_id (StratifiedGroupKFold); MHIST has
    no patient ids -> patch-level StratifiedKFold (flagged, unavoidable).

Then correlate CONSENSUS vs DOWNSTREAM across encoders:
  * per-dataset Spearman (consistency)
  * aggregate: mean-consensus vs mean-AUC across datasets, Spearman + bootstrap CI
  * bonus (Claim B): cross-dataset consensus-ranking stability (Kendall's W)

Outputs (results/):
  phase11_per_dataset.csv        (dataset, encoder, consensus, auc, n_used, cv_mode)
  phase11_encoder_summary.csv    (encoder, mean_consensus, mean_auc, per-dataset ...)
  phase11_correlations.csv       (per-dataset + aggregate rho, p, CI, Kendall W)
  plot_phase11_money.png
"""
import os, sys, time, argparse, glob, itertools
import numpy as np, pandas as pd, h5py
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import normalize, StandardScaler, LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from scipy.stats import spearmanr
import warnings; warnings.filterwarnings("ignore")
try:
    from sklearn.model_selection import StratifiedGroupKFold
    HAS_SGK = True
except Exception:
    from sklearn.model_selection import GroupKFold, StratifiedKFold
    HAS_SGK = False
from sklearn.model_selection import StratifiedKFold

from config import META, FEAT, OUT, EXCLUDE

ap = argparse.ArgumentParser()
ap.add_argument("--datasets", nargs="+",
                default=["MHIST", "CHAOYANG", "Kather-MSI-CRC", "Kather-MSI-STAD", "TCGA-TILs"])
ap.add_argument("--consensus_n", type=int, default=10000, help="subsample for kNN consensus")
ap.add_argument("--probe_n", type=int, default=40000, help="cap patches for downstream CV")
ap.add_argument("--k", type=int, default=10)
ap.add_argument("--folds", type=int, default=5)
ap.add_argument("--boot", type=int, default=10000)
ap.add_argument("--seed", type=int, default=42)
args = ap.parse_args()
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(args.seed)

def encoders_for(ds):
    encs = []
    for p in sorted(glob.glob(os.path.join(FEAT, ds, "features_*.h5"))):
        e = os.path.basename(p)[len("features_"):-3]
        if e not in EXCLUDE:
            encs.append(e)
    return encs

def load_feat(ds, enc):
    with h5py.File(os.path.join(FEAT, ds, f"features_{enc}.h5"), "r") as f:
        return f["features"][:]

def stratified_subsample(y, groups, cap):
    """Pick <=cap indices, proportional per class, seed-fixed. Groups kept via splitter."""
    idx = np.arange(len(y))
    if cap is None or len(y) <= cap:
        return idx
    keep = []
    for c in np.unique(y):
        ci = idx[y == c]
        take = max(1, int(round(cap * len(ci) / len(y))))
        keep.append(rng.choice(ci, min(take, len(ci)), replace=False))
    return np.sort(np.concatenate(keep))

def mutual_knn_consensus(feat_by_enc, k):
    encs = list(feat_by_enc)
    knn = {}
    for e in encs:
        Z = normalize(feat_by_enc[e].astype("float32"), axis=1)
        nn = NearestNeighbors(n_neighbors=k + 1, metric="cosine", n_jobs=-1).fit(Z)
        knn[e] = nn.kneighbors(Z, return_distance=False)[:, 1:]
    N = len(next(iter(feat_by_enc.values())))
    agree = {e: [] for e in encs}
    for a, b in itertools.combinations(encs, 2):
        Ia, Ib = knn[a], knn[b]
        inter = sum(len(np.intersect1d(Ia[i], Ib[i], assume_unique=True)) for i in range(N)) / (N * k)
        agree[a].append(inter); agree[b].append(inter)
    return {e: float(np.mean(agree[e])) for e in encs}

def probe_auc(X, y, groups, folds):
    """Patient-grouped (or patch-level) CV macro-AUC."""
    classes = np.unique(y)
    multiclass = len(classes) > 2
    use_group = groups is not None and len(np.unique(groups)) >= folds
    if use_group and HAS_SGK:
        splitter = StratifiedGroupKFold(n_splits=folds, shuffle=True, random_state=args.seed)
        split = splitter.split(X, y, groups)
        mode = "patient-grouped"
    elif use_group:
        splitter = GroupKFold(n_splits=folds); split = splitter.split(X, y, groups); mode = "patient-grouped(GKF)"
    else:
        splitter = StratifiedKFold(n_splits=folds, shuffle=True, random_state=args.seed)
        split = splitter.split(X, y); mode = "patch-level"
    aucs = []
    for tr, te in split:
        sc = StandardScaler().fit(X[tr])
        clf = LogisticRegression(max_iter=500, n_jobs=-1,
                                 multi_class="ovr" if multiclass else "auto")
        clf.fit(sc.transform(X[tr]), y[tr])
        if len(np.unique(y[te])) < 2:
            continue
        proba = clf.predict_proba(sc.transform(X[te]))
        if multiclass:
            if len(clf.classes_) != len(classes):
                continue
            aucs.append(roc_auc_score(y[te], proba, multi_class="ovr", labels=clf.classes_))
        else:
            aucs.append(roc_auc_score(y[te], proba[:, 1]))
    return (float(np.mean(aucs)) if aucs else np.nan), mode

# ---- main ----
t0 = time.time()
per_rows = []
consensus_by_ds = {}
for ds in args.datasets:
    print(f"\n{'='*60}\n{ds}\n{'='*60}", flush=True)
    encs = encoders_for(ds)
    df = pd.read_csv(os.path.join(META, ds, "metadata.csv"))
    df = df.reset_index(drop=True)
    valid = df["label"].notna().values
    y_all = LabelEncoder().fit_transform(df["label"].astype(str).values)
    pid = df["patient_id"].astype(str).str.strip().replace({"nan": ""}).values
    has_pid = (pid != "").sum() == len(pid) and len(set(pid)) > 1

    # one shared subsample per dataset (same patches for all encoders)
    sub_probe = stratified_subsample(y_all[valid], pid[valid] if has_pid else None, args.probe_n)
    base_idx = np.arange(len(df))[valid]
    probe_idx = base_idx[sub_probe]
    cons_idx = probe_idx if len(probe_idx) <= args.consensus_n else \
        np.sort(rng.choice(probe_idx, args.consensus_n, replace=False))
    print(f"  encoders={len(encs)}  N={len(df)}  probe_n={len(probe_idx)}  consensus_n={len(cons_idx)}"
          f"  patients={'yes' if has_pid else 'NONE (patch-level)'}", flush=True)

    # consensus features (subsampled) for all encoders
    feat_cons, feat_probe = {}, {}
    for e in encs:
        F = load_feat(ds, e)
        if len(F) != len(df):
            print(f"    [!] {e}: len {len(F)}!={len(df)}, skip"); continue
        feat_cons[e] = F[cons_idx]
        feat_probe[e] = F[probe_idx].astype("float32")
        del F
    encs = list(feat_probe)  # keep only aligned encoders

    print("  computing Mutual-kNN consensus ...", flush=True)
    cons = mutual_knn_consensus(feat_cons, args.k)
    consensus_by_ds[ds] = cons

    yg = y_all[probe_idx]; gg = pid[probe_idx] if has_pid else None
    for e in encs:
        auc, mode = probe_auc(feat_probe[e], yg, gg, args.folds)
        per_rows.append({"dataset": ds, "encoder": e, "consensus": cons[e],
                         "auc": auc, "n_used": len(probe_idx), "cv_mode": mode})
        print(f"    {e:15s} consensus={cons[e]:.4f}  AUC={auc:.4f}  [{mode}]", flush=True)

per = pd.DataFrame(per_rows)
per.to_csv(os.path.join(OUT, "phase11_per_dataset.csv"), index=False)

# ---- aggregate per encoder ----
summ = per.pivot_table(index="encoder", values=["consensus", "auc"], aggfunc="mean")
summ.columns = ["mean_auc", "mean_consensus"]
cons_wide = per.pivot(index="encoder", columns="dataset", values="consensus").add_prefix("cons_")
auc_wide  = per.pivot(index="encoder", columns="dataset", values="auc").add_prefix("auc_")
summ = summ.join(cons_wide).join(auc_wide).reset_index()
summ.to_csv(os.path.join(OUT, "phase11_encoder_summary.csv"), index=False)

# ---- correlations ----
corr_rows = []
for ds in args.datasets:
    s = per[per.dataset == ds].dropna(subset=["auc"])
    if len(s) >= 4:
        r, p = spearmanr(s.consensus, s.auc)
        corr_rows.append({"scope": ds, "n": len(s), "rho": r, "p": p})
agg = summ.dropna(subset=["mean_auc", "mean_consensus"])
rho, p = spearmanr(agg.mean_consensus, agg.mean_auc)
# bootstrap CI over encoders
xs, ys = agg.mean_consensus.values, agg.mean_auc.values
boots = []
for _ in range(args.boot):
    b = rng.integers(0, len(xs), len(xs))
    if len(np.unique(xs[b])) > 2:
        boots.append(spearmanr(xs[b], ys[b])[0])
lo, hi = np.percentile(boots, [2.5, 97.5])
corr_rows.append({"scope": "AGGREGATE(mean)", "n": len(agg), "rho": rho, "p": p,
                  "ci_lo": lo, "ci_hi": hi})

# Kendall's W across dataset consensus rankings (Claim B: stability)
rank_mat = cons_wide.rank(ascending=False)
m, n_ = rank_mat.shape[1], rank_mat.shape[0]
Rj = rank_mat.sum(axis=1); S = ((Rj - Rj.mean())**2).sum()
kendall_w = 12 * S / (m**2 * (n_**3 - n_))
corr_rows.append({"scope": "Kendall_W_consensus_stability", "n": n_, "rho": kendall_w, "p": np.nan})
pd.DataFrame(corr_rows).to_csv(os.path.join(OUT, "phase11_correlations.csv"), index=False)

print("\n" + "="*60)
print("PER-DATASET Spearman(consensus, AUC):")
for c in corr_rows:
    if c["scope"] in args.datasets:
        print(f"  {c['scope']:16s} rho={c['rho']:+.3f}  p={c['p']:.3f}  n={c['n']}")
print(f"\nAGGREGATE  Spearman={rho:+.3f}  p={p:.4f}  95%CI=[{lo:+.3f},{hi:+.3f}]  n={len(agg)}")
print(f"Consensus cross-dataset stability  Kendall W={kendall_w:.3f}")

# ---- money plot ----
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(9, 7))
ax.scatter(xs, ys, s=70, c="#2b6cb0", edgecolors="black", linewidth=0.6, zorder=3)
for _, r in agg.iterrows():
    ax.annotate(r.encoder, (r.mean_consensus, r.mean_auc), fontsize=7,
                alpha=0.8, xytext=(3, 3), textcoords="offset points")
# rank-fit trend line
order = np.argsort(xs)
if len(xs) > 2:
    z = np.polyfit(xs, ys, 1); ax.plot(np.sort(xs), np.polyval(z, np.sort(xs)),
                                       "--", color="gray", alpha=0.7, zorder=2)
ax.set_xlabel("Label-free Mutual-kNN Consensus  (mean across hard datasets)")
ax.set_ylabel("Downstream macro-AUC  (patient-grouped CV, mean)")
ax.set_title(f"Phase 11 — Money Plot\nSpearman ρ = {rho:+.3f}  (95% CI [{lo:+.2f}, {hi:+.2f}], p={p:.3f}, n={len(agg)})",
             fontweight="bold")
ax.grid(alpha=0.25)
plt.tight_layout(); plt.savefig(os.path.join(OUT, "plot_phase11_money.png"), dpi=150)
print(f"\n[SAVED] plot_phase11_money.png  |  done in {time.time()-t0:.0f}s")
