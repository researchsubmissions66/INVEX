"""
Label-free encoder-quality metric family (Pillar A: agreement / consensus).
All functions operate on CACHED features — no labels, no training.

Conventions:
  feat_dict : {encoder_name -> np.ndarray [N, d]}  (same N, shared patch sample)
  knn_dict  : {encoder_name -> np.ndarray [N, k]}  (int neighbor indices, self excluded)
  A         : [M, M] symmetric mutual-kNN overlap matrix in [0,1]
"""
import numpy as np
from collections import Counter
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import normalize


# ---------- graph construction ----------
def build_knn(feat, k, metric="cosine"):
    Z = normalize(feat.astype("float32"), axis=1) if metric == "cosine" else feat.astype("float32")
    nn = NearestNeighbors(n_neighbors=k + 1, metric=metric, n_jobs=-1).fit(Z)
    return nn.kneighbors(Z, return_distance=False)[:, 1:]  # drop self


def mutual_knn_matrix(knn_dict, k):
    encs = list(knn_dict)
    M, N = len(encs), knn_dict[encs[0]].shape[0]
    sets = {e: [set(row.tolist()) for row in knn_dict[e]] for e in encs}
    A = np.eye(M)
    for a in range(M):
        for b in range(a + 1, M):
            sa, sb = sets[encs[a]], sets[encs[b]]
            inter = sum(len(sa[i] & sb[i]) for i in range(N)) / (N * k)
            A[a, b] = A[b, a] = inter
    return A, encs


# ---------- A0: mean consensus (degree centrality) ----------
def mean_consensus(A):
    M = A.shape[0]
    off = A.sum(1) - np.diag(A)
    return off / (M - 1)


# ---------- A1: eigen-consensus ----------
def eigen_consensus(A, chance=0.0):
    B = np.clip(A - chance, 0, None).copy()
    np.fill_diagonal(B, 0.0)
    w, V = np.linalg.eigh(B)          # ascending; leading = last
    c = np.abs(V[:, -1])              # Perron–Frobenius: sign-definite
    s = c.sum()
    return c / s if s > 0 else c


# ---------- A2: redundancy-adjusted consensus ----------
def redundancy_adjusted_consensus(A, tau=None):
    M = A.shape[0]
    off = A[~np.eye(M, dtype=bool)]
    if tau is None:
        tau = np.quantile(off, 0.90)          # "near-duplicate" threshold
    dup = (A > tau).sum(1)                     # incl. self ⇒ >=1
    w = 1.0 / np.maximum(dup, 1)
    scores = np.zeros(M)
    for i in range(M):
        mask = np.ones(M, bool); mask[i] = False
        scores[i] = np.sum(w[mask] * A[i, mask]) / np.sum(w[mask])
    return scores, tau


# ---------- A3: consensus-graph recovery (leave-one-out) ----------
def consensus_graph_recovery(knn_dict, k):
    encs = list(knn_dict)
    M, N = len(encs), knn_dict[encs[0]].shape[0]
    scores = {e: 0.0 for e in encs}
    for i in range(N):
        per_e = {e: knn_dict[e][i] for e in encs}
        votes = Counter()
        for e in encs:
            votes.update(per_e[e].tolist())
        for e in encs:
            v = votes.copy()
            for j in per_e[e].tolist():
                v[j] -= 1                       # leave-one-out
            top = [j for j, c in v.most_common() if j != i and c > 0][:k]
            if top:
                inter = len(set(per_e[e].tolist()) & set(top))
                scores[e] += inter / k
    return np.array([scores[e] / N for e in encs]), encs


# ---------- A4a: CKA-consensus (linear, feature-space form) ----------
def _linear_cka(Xa, Xb):
    Xa = Xa - Xa.mean(0, keepdims=True)
    Xb = Xb - Xb.mean(0, keepdims=True)
    hsic = np.linalg.norm(Xa.T @ Xb) ** 2
    na = np.linalg.norm(Xa.T @ Xa)
    nb = np.linalg.norm(Xb.T @ Xb)
    return hsic / (na * nb + 1e-12)


def cka_matrix(feat_dict, n_sub=10000, seed=0):
    encs = list(feat_dict)
    N = len(feat_dict[encs[0]])
    rng = np.random.default_rng(seed)
    idx = rng.choice(N, min(n_sub, N), replace=False)
    Zs = {e: feat_dict[e][idx].astype("float32") for e in encs}
    M = len(encs); C = np.eye(M)
    for a in range(M):
        for b in range(a + 1, M):
            C[a, b] = C[b, a] = _linear_cka(Zs[encs[a]], Zs[encs[b]])
    return C, encs


# ---------- A4b: RSA-consensus (global distance-matrix agreement) ----------
def _rank(x):
    order = x.argsort()
    r = np.empty_like(order, dtype=float)
    r[order] = np.arange(len(x))
    return r


def rsa_consensus(feat_dict, n_sub=3000, seed=0):
    encs = list(feat_dict)
    N = len(feat_dict[encs[0]])
    rng = np.random.default_rng(seed)
    idx = rng.choice(N, min(n_sub, N), replace=False)
    iu = np.triu_indices(len(idx), k=1)
    dvecs = {}
    for e in encs:
        Z = normalize(feat_dict[e][idx].astype("float32"), axis=1)
        D = 1.0 - (Z @ Z.T)                     # cosine distance
        dvecs[e] = _rank(D[iu])                 # rank once for Spearman
    scores = []
    for e in encs:
        others = np.mean([dvecs[o] for o in encs if o != e], axis=0)
        ro = _rank(others)
        a, b = dvecs[e] - dvecs[e].mean(), ro - ro.mean()
        scores.append(float((a @ b) / (np.sqrt((a @ a) * (b @ b)) + 1e-12)))
    return np.array(scores), encs
