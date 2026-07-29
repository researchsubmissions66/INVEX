"""Shared helpers for the analysis/figure scripts: repo-root bootstrap, palettes, subsets."""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)                       # makes config / utils importable from any cwd

import numpy as np, pandas as pd
from config import OUT, FAMILY, VLM

FIGDIR = os.path.join(ROOT, "figures")
os.makedirs(FIGDIR, exist_ok=True)

# family palette (kept consistent across every figure)
FAM_COLOR  = {"path_ssl": "#2b6cb0", "path_vlm": "#d69e2e", "path_other": "#38a169", "baseline": "#c53030"}
FAM_MARKER = {"path_ssl": "o",       "path_vlm": "s",       "path_other": "D",       "baseline": "^"}
FAM_LABEL  = {"path_ssl": "pathology SSL", "path_vlm": "vision-language",
              "path_other": "contrastive (CTransPath)", "baseline": "baseline (ImageNet/VLM)"}

METRICS_CSV = os.path.join(OUT, "encoder_metrics.csv")


def load_metrics(require_invariance=True):
    """Load the master per-encoder metrics table (build with analysis/build_metrics_table.py)."""
    if not os.path.exists(METRICS_CSV):
        raise SystemExit(f"missing {METRICS_CSV} — run: python analysis/build_metrics_table.py")
    d = pd.read_csv(METRICS_CSV).set_index("encoder")
    return d.dropna(subset=["retention", "effrank", "auc"]) if require_invariance else d


def vision_only(df):
    """The headline subset: invariance roster minus the vision-language models."""
    return df[~df.index.isin(VLM)]


def zscore(s):
    return (s - s.mean()) / (s.std() + 1e-9)
