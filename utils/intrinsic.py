"""
Off-the-shelf LABEL-FREE intrinsic-geometry metrics (CPU, cached features only).
These are single-encoder (non-relational) — the BASELINES the agreement family is
meant to beat. Adapted from plan.md Part E. Oriented so higher = putatively better
(uniformity negated), except alpha_req/twonn_id which are reported raw (interpret sign).

Caveat (plan.md Phase 1): effrank / coding_rate / twonn_id scale with embedding dim d,
which differs across encoders -> report raw AND d-normalized; treat cross-encoder
comparisons as dimension-confounded (that confound is part of the story).
"""
import numpy as np
from numpy.linalg import svd, eigh, slogdet
from sklearn.neighbors import NearestNeighbors


def effective_rank(Z, eps=1e-7):
    """RankMe effective rank = entropy of the singular-value distribution."""
    Zc = Z - Z.mean(0, keepdims=True)
    s = svd(Zc, compute_uv=False)
    p = s / (s.sum() + eps) + eps
    return float(np.exp(-(p * np.log(p)).sum()))


def kappa(Rbar, d):
    """Banerjee et al. (2005) vMF concentration MLE from mean resultant length Rbar in dimension d."""
    Rbar = np.clip(Rbar, 1e-4, 1 - 1e-6)
    return Rbar * (d - Rbar**2) / (1 - Rbar**2)


def alpha_req(Z, lo_frac=0.05, hi_frac=0.5):
    """Power-law exponent of eigenspectrum decay (lambda_i ~ i^-alpha); alpha~1 = good."""
    Zc = Z - Z.mean(0, keepdims=True)
    cov = (Zc.T @ Zc) / (Zc.shape[0] - 1)
    w = np.sort(eigh(cov)[0])[::-1]
    w = w[w > 0]
    n = len(w)
    i0, i1 = max(1, int(lo_frac * n)), max(3, int(hi_frac * n))
    x = np.log(np.arange(i0, i1) + 1.0)
    y = np.log(w[i0:i1])
    A = np.vstack([x, np.ones_like(x)]).T
    slope = np.linalg.lstsq(A, y, rcond=None)[0][0]
    return float(-slope)


def twonn_id(Z, trim=0.1):
    """TwoNN MLE intrinsic dimension with tail trimming."""
    nn = NearestNeighbors(n_neighbors=3, n_jobs=-1).fit(Z)
    d, _ = nn.kneighbors(Z)
    mu = d[:, 2] / np.clip(d[:, 1], 1e-12, None)
    mu = np.sort(mu[mu > 1.0])
    mu = mu[: int((1 - trim) * len(mu))]
    return float(len(mu) / np.log(mu).sum())


def uniformity(Z, t=2.0, n_pairs=200_000, seed=0):
    """Wang-Isola uniformity on the unit sphere (raw: lower = more uniform)."""
    rng = np.random.default_rng(seed)
    Zn = Z / (np.linalg.norm(Z, axis=1, keepdims=True) + 1e-12)
    i = rng.integers(0, len(Zn), n_pairs); j = rng.integers(0, len(Zn), n_pairs)
    sq = ((Zn[i] - Zn[j]) ** 2).sum(1)
    return float(np.log(np.exp(-t * sq).mean() + 1e-12))


def coding_rate(Z, eps2=0.5):
    """Total coding rate R = 0.5 logdet(I + d/(M eps^2) Z^T Z)."""
    M, d = Z.shape
    Zc = Z - Z.mean(0, keepdims=True)
    G = (d / (M * eps2)) * (Zc.T @ Zc)
    _, ld = slogdet(np.eye(d) + G)
    return float(0.5 * ld)


def all_intrinsic(Z):
    """Return oriented dict (higher=putatively better; uniformity negated)."""
    Z = Z.astype("float32")
    d = Z.shape[1]
    er = effective_rank(Z)
    cr = coding_rate(Z)
    tid = twonn_id(Z)
    return {
        "I_effrank": er,
        "I_effrank_norm": er / d,
        "I_alpha_req": alpha_req(Z),
        "I_twonn_id": tid,
        "I_neg_uniformity": -uniformity(Z),   # oriented: higher = more uniform = better
        "I_coding_rate": cr,
        "I_coding_rate_norm": cr / d,
    }
