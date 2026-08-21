"""
Generate the two paper reference tables, so they never drift from config/data:
  docs/datasets.csv  — per dataset: organ, task, #classes, class:count, patches, patients, mag
  docs/encoders.csv  — per encoder: family, backbone, paradigm, dim, invariance-roster flag
Descriptive columns (organ/task/backbone/paradigm) live here; counts/dims are read from disk.
"""
import os, glob
import pandas as pd, h5py
from _common import ROOT
from config import DATASETS, META, FEAT, FAMILY, VLM

DOCS = os.path.join(ROOT, "docs")

DS_INFO = {  # organ, task-type
 "MHIST": ("colorectal", "polyp type (HP vs SSA)"),
 "CHAOYANG": ("colon", "tissue type"),
 "WSSS4LUAD": ("lung adeno.", "tissue type"),
 "NCT-CRC-VAL-HE-7K": ("colorectal", "tissue type (9-class, val)"),
 "BreaKHis": ("breast", "tumor benign/malignant"),
 "LC25000_COLON": ("colon", "tumor benign/adeno."),
 "SICAPv2": ("prostate", "Gleason grading"),
 "LC25000_LUNG": ("lung", "tumor subtype (3-class)"),
 "CCRCC_Lymphocyte": ("kidney (ccRCC)", "immune vs tumor"),
 "CCRCC_Tissue": ("kidney (ccRCC)", "tissue type (6-class)"),
 "digestPath": ("colon/GI", "lesion cancerous/non"),
 "NCT-CRC": ("colorectal", "tissue type (9-class, train)"),
 "Kather-MSI-CRC": ("colorectal", "molecular MSI/MSS"),
 "Kather-MSI-STAD": ("stomach", "molecular MSI/MSS"),
 "TCGA-TILs": ("pan-cancer", "TIL detection"),
 "PCAM": ("lymph node", "metastasis normal/tumor"),
}

ENC_INFO = {  # backbone, paradigm  (see docs; pretraining-scale figures approximate)
 "uni_v1": ("ViT-L/16", "DINOv2"), "uni_v2": ("ViT-H/14", "DINOv2"),
 "virchow": ("ViT-H/14", "DINOv2"), "virchow2": ("ViT-H/14", "DINOv2"),
 "gigapath": ("ViT-g/14", "DINOv2"), "hoptimus0": ("ViT-g/14", "DINOv2-style"),
 "hoptimus1": ("ViT-g/14", "DINOv2-style"), "h0-mini": ("ViT-B/14", "distillation"),
 "kaiko-vits8": ("ViT-S/8", "DINO"), "kaiko-vits16": ("ViT-S/16", "DINO"),
 "kaiko-vitb8": ("ViT-B/8", "DINO"), "kaiko-vitb16": ("ViT-B/16", "DINO"),
 "kaiko-vitl14": ("ViT-L/14", "DINOv2"), "midnight12k": ("ViT-L/14", "DINOv2 (Midnight)"),
 "openmidnight": ("ViT-L/14", "DINOv2 (open Midnight)"), "phikon": ("ViT-B/16", "iBOT"),
 "phikon_v2": ("ViT-L/16", "DINOv2"), "hibou_l": ("ViT-L/14", "DINOv2"),
 "gpfm": ("ViT-L", "multi-teacher distillation"), "lunit-vits8": ("ViT-S/8", "DINO"),
 "genbio-pathfm": ("ViT (large)", "SSL"),
 "conch_v1": ("ViT-B/16", "vision-language"), "conch_v15": ("ViT", "vision-language"),
 "musk": ("ViT-L", "vision-language"),
 "ctranspath": ("CNN+Swin-T", "SRCL contrastive"),
 "resnet50": ("ResNet-50", "ImageNet supervised"),
 "gemma4-e4b": ("Gemma-3n tower", "general VLM"), "gemma4-26b": ("Gemma tower", "general VLM"),
}


def datasets_csv():
    rows = []
    for ds in DATASETS:
        d = pd.read_csv(os.path.join(META, ds, "metadata.csv"))
        vc = d["label"].astype(str).value_counts().sort_index()
        npat = d["patient_id"].nunique() if "patient_id" in d and d["patient_id"].notna().any() else 0
        organ, task = DS_INFO.get(ds, ("?", "?"))
        rows.append({"dataset": ds, "organ": organ, "task": task, "n_classes": vc.size,
                     "classes": "; ".join(f"{k}:{v}" for k, v in vc.items()),
                     "n_patches": len(d), "n_patients": ("per-patch" if npat == len(d) else (npat or "none")),
                     "magnification": ",".join(sorted(d["magnification"].astype(str).unique())) if "magnification" in d else "?"})
    p = os.path.join(DOCS, "datasets.csv"); pd.DataFrame(rows).to_csv(p, index=False)
    print(f"[SAVED] {p} ({len(rows)} datasets)")


def encoders_csv():
    inv = set(os.path.basename(f)[len("invariance_"):-4]
              for f in glob.glob(os.path.join(ROOT, "results", "invariance_*.csv")) if "summary" not in f)
    rows = []
    for e in sorted(FAMILY, key=lambda x: (FAMILY[x], x)):
        dim = None
        for p in glob.glob(os.path.join(FEAT, "*", f"features_{e}.h5")):
            with h5py.File(p, "r") as f: dim = f["features"].shape[1]; break
        bb, para = ENC_INFO.get(e, ("?", "?"))
        rows.append({"encoder": e, "family": FAMILY[e], "backbone": bb, "paradigm": para,
                     "dim": dim, "in_invariance_roster": e in inv,
                     "in_vision_only": (e in inv) and (e not in VLM)})
    p = os.path.join(DOCS, "encoders.csv"); pd.DataFrame(rows).to_csv(p, index=False)
    print(f"[SAVED] {p} ({len(rows)} encoders; invariance roster n={sum(r['in_invariance_roster'] for r in rows)})")


if __name__ == "__main__":
    datasets_csv(); encoders_csv()
