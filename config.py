"""Central configuration for INVEX: paths, dataset roster, encoder family map, subsets.

These were previously copy-pasted across the phase scripts (paths in all of them,
DATASETS in 3, the 28-encoder FAMILY map in 3). Single source of truth now.
"""
import os

# ---- paths ----
ROOT = os.path.dirname(os.path.abspath(__file__))                 # .../PathAudit
FEAT = "/path/to/PATCH_Features"                                  # cached patch features (per dataset)
META = "/path/to/Dataset/Additional/Dataset_Downloads/RAW_DATA_Cleaned"
OUT  = os.path.join(ROOT, "results")

# ---- the 16 patch datasets (single native resolution) ----
DATASETS = ["MHIST", "CHAOYANG", "WSSS4LUAD", "NCT-CRC-VAL-HE-7K", "BreaKHis", "LC25000_COLON",
            "SICAPv2", "LC25000_LUNG", "CCRCC_Lymphocyte", "CCRCC_Tissue", "digestPath", "NCT-CRC",
            "Kather-MSI-CRC", "Kather-MSI-STAD", "TCGA-TILs", "PCAM"]

# ---- encoder -> family (architecture / training paradigm) ----
FAMILY = {
    **{e: "path_ssl" for e in [
        "uni_v1", "uni_v2", "virchow", "virchow2", "hoptimus0", "hoptimus1", "h0-mini",
        "kaiko-vitb8", "kaiko-vitb16", "kaiko-vits16", "kaiko-vits8", "kaiko-vitl14",
        "midnight12k", "openmidnight", "phikon", "phikon_v2", "gigapath", "hibou_l",
        "gpfm", "lunit-vits8", "genbio-pathfm"]},
    **{e: "path_vlm" for e in ["conch_v1", "conch_v15", "musk"]},
    "ctranspath": "path_other",
    **{e: "baseline" for e in ["resnet50", "gemma4-e4b", "gemma4-26b"]},
}

# ---- subsets used for the headline correlations ----
# VLMs (text-aligned geometry) + gemma baselines are dropped for the "vision-only" headline (n=22).
VLM = {"conch_v1", "conch_v15", "musk", "gemma4-e4b", "gemma4-26b"}

EXCLUDE = {"keep"}   # non-encoder feature dirs to skip
