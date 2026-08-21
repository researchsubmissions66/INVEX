<div align="center">
  <img src="figures/logo.png" width="500" alt="INVEX Logo">
</div>

# INVEX: Label-Free Pathology Foundation Model Ranking via Invariance and Expressiveness

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![PyTorch 2.0+](https://img.shields.io/badge/PyTorch-2.0+-ee4c2c.svg)](https://pytorch.org/)

**INVEX** is a framework that provides a purely **intrinsic, label-free** score to predict downstream performance across pathology foundation models — with no labels and no fine-tuning. A good tissue encoder *collapses* label-preserving nuisance (rotational invariance, because tissue has no canonical orientation) while *spreading* distinct biology apart (representational discriminability / effective rank). INVEX measures exactly this.


---

## 🚀 Key Features

- **Label-Free Ranking**: Predicts downstream oracle performance without needing any labels or fine-tuning.
- **Massive Scale**: Evaluated across **22 pathology foundation models** and **16 public patch-level benchmarks** covering 8+ organs and >1.2M patches.
- **Probabilistic Scoring**: Uses von Mises–Fisher (vMF) concentration parameters to model invariance and expressiveness on the unit hypersphere, with Bayesian-bootstrap credible intervals.

---

## 📦 Installation

```bash
# Clone the repository
git clone https://github.com/researchsubmissions66/INVEX.git
cd INVEX

# Create environment
conda env create -f environment.yml
conda activate invex

# Or via pip:
pip install -r requirements.txt

# GPU stage only (rotated re-embedding, invariance):
pip install torch==2.5.1 timm==0.9.16
```

---

## 📂 Project Structure

```text
INVEX/
├── analysis/          # Figure generation & reporting scripts
├── pipeline/          # Pipeline phases (run via main.py)
├── utils/             # Pure metric primitives (effective_rank, kappa/vMF, retention, augmentations)
├── config.py          # Single source of truth: paths, dataset roster, encoder family map
├── main.py            # CLI dispatcher
└── Makefile           # One-command reproduction
```

---

## 🔬 Encoders (22 Models)

INVEX evaluates **22 pathology foundation models**:

### Pathology Foundation Models
| Encoder | Backbone | Training | Dim |
| :--- | :--- | :--- | :---: |
| `UNI-v1` | ViT-L/16 | DINOv2 | 1024 |
| `UNI-v2` | ViT-H/14 | DINOv2 | 1536 |
| `Virchow` | ViT-H/14 | DINOv2 | 2560 |
| `Virchow2` | ViT-H/14 | DINOv2 | 2560 |
| `GigaPath` | ViT-g/14 | DINOv2 | 1536 |
| `H-Optimus-0` | ViT-g/14 | DINOv2-style | 1536 |
| `H-Optimus-1` | ViT-g/14 | DINOv2-style | 1536 |
| `Phikon` | ViT-B/16 | iBOT | 768 |
| `Phikon-v2` | ViT-L/16 | DINOv2 | 1024 |
| `Hibou-L` | ViT-L/14 | DINOv2 | 1024 |
| `GPFM` | ViT-L | Multi-teacher distillation | 1024 |
| `H0-mini` | ViT-B/14 | Distillation | 768 |
| `Midnight-12k` | ViT-L/14 | DINOv2 (Midnight) | 1536 |
| `OpenMidnight` | ViT-L/14 | DINOv2 (open Midnight) | 1536 |
| `Kaiko-ViT-B/8` | ViT-B/8 | DINO | 768 |
| `Kaiko-ViT-B/16` | ViT-B/16 | DINO | 768 |
| `Kaiko-ViT-S/8` | ViT-S/8 | DINO | 384 |
| `Kaiko-ViT-S/16` | ViT-S/16 | DINO | 384 |
| `Kaiko-ViT-L/14` | ViT-L/14 | DINOv2 | 1024 |
| `Lunit-ViT-S/8` | ViT-S/8 | DINO | 384 |
| `GenBio-PathFM` | ViT (large) | SSL | 4608 |
| `CTransPath` | CNN+Swin-T | SRCL contrastive | 768 |

---

## 🧬 Patch-Level Datasets (16 Benchmarks)


### Dataset Summary

| Dataset | Source / Institution | Description | Link |
| :--- | :--- | :--- | :--- |
| **Tumor Detection** | | | |
| LC25000 | University of South Florida / TampaPath | Created from a small collection of pathology images that were extensively augmented to produce 25,000 images across five tissue classes. | [Link](https://github.com/tampapath/lc25000) |
| BreakHis | Federal University of Paraná (UFPR), Brazil | Histopathology microscopy dataset collected from 82 patients at four magnifications (40×, 100×, 200×, and 400×), with expert-confirmed benign and malignant diagnoses. | [Link](https://web.inf.ufpr.br/vri/databases/breakhis/) |
| PCAM (PatchCamelyon) | Derived from the CAMELYON16 Grand Challenge (Radboud UMC and UMC Utrecht) | 96×96 image patches extracted from whole-slide images with binary labels indicating metastatic tissue. | [Link](https://github.com/basveeling/pcam) |
| DigestPath | DigestPath Grand Challenge (2019) | Public benchmark consisting of pathology images collected for gastrointestinal pathology tasks, including benign and malignant lesion classification. | [Link](https://digestpath2019.grand-challenge.org/) |
| **Molecular Status Prediction** | | | |
| Kather-MSI-STAD | University Hospital Heidelberg | Clinical cohort assembled from TCGA and additional institutional data for predicting microsatellite instability directly from H&E slides. | [Link](https://doi.org/10.5281/zenodo.2530835) |
| Kather-MSI-CRC | University Hospital Heidelberg | Clinical and TCGA-derived colorectal cancer cohort developed for microsatellite instability prediction from histopathology. | [Link](https://doi.org/10.5281/zenodo.1214456) |
| **Immune / TIL Assessment** | | | |
| CCRCC-Lymphocyte | TCGA-KIRC derived research dataset | Image patches extracted from TCGA whole-slide images and annotated for lymphocyte infiltration assessment. | [Link](https://portal.gdc.cancer.gov/projects/TCGA-KIRC) |
| TCGA-TILs | The Cancer Genome Atlas (TCGA) | Pan-cancer whole-slide image collection with tumor-infiltrating lymphocyte (TIL) annotations for immune profiling studies. | [Link](https://gdc.cancer.gov/) |
| **Tissue Typing** | | | |
| WSSS4LUAD | WSSS4LUAD Grand Challenge; Guangdong Provincial People's Hospital (GDPH) and TCGA | Weakly supervised tissue segmentation benchmark. Training uses patch-level labels, while validation and test pixel-level annotations were generated through a pathologist-in-the-loop annotation pipeline. | [Link](https://github.com/DEEPBIO/WSSS4LUAD) |
| CHAOYANG | Beijing Chaoyang Hospital | Clinical pathology image dataset manually annotated by expert pathologists for tissue classification. | [Link](https://bupt-ai-cz.github.io/BCaM/) |
| NCT-CRC-HE-100K | National Center for Tumor Diseases (NCT) Biobank and University Medical Center Mannheim | 100,000 manually annotated tissue patches extracted from 86 whole-slide images and categorized into nine tissue classes. | [Link](https://zenodo.org/records/1214456) |
| NCT-CRC-VAL-HE-7K | National Center for Tumor Diseases (NCT), Heidelberg | Independent validation cohort created using the same extraction and annotation protocol as NCT-CRC-HE-100K. | [Link](https://zenodo.org/records/1214456) |
| CCRCC-Tissue | TCGA-KIRC derived research dataset | Whole-slide image patches extracted from TCGA and manually assigned tissue-type labels including tumor, stroma, and necrosis. | [Link](https://portal.gdc.cancer.gov/projects/TCGA-KIRC) |
| **Tumor Subtyping / Grading** | | | |
| MHIST | Dartmouth-Hitchcock Medical Center | Curated clinical dataset with expert-consensus annotations distinguishing hyperplastic polyps from sessile serrated adenomas. | [Link](https://bmirds.github.io/MHIST/) |
| SICAPv2 | Hospital de Braga and University of Minho, Portugal | Expert-annotated prostate biopsy whole-slide images with Gleason grading for automated pathology analysis. | [Link](https://github.com/josegcpa/SICAPv2) |

### Dataset Classes

| Dataset | Class Labels | Description |
| :--- | :--- | :--- |
| **Tumor Detection** | | |
| LC25000-LUNG | Adenocarcinoma (ACA), Benign Lung (N), Squamous Cell Carcinoma (SCC) | **Task:** Lung tissue classification<br>**N:** Benign lung parenchyma<br>**ACA:** Glandular epithelial carcinoma<br>**SCC:** Squamous epithelial carcinoma. |
| LC25000-COLON | Adenocarcinoma (ACA), Benign Colon (N) | **Task:** Benign vs. malignant colon tissue<br>**N:** Normal colonic mucosa<br>**ACA:** Invasive colorectal adenocarcinoma. |
| BreakHis | Benign, Malignant | **Task:** Breast tumor classification<br>**Benign:** Non-invasive breast lesions<br>**Malignant:** Invasive breast carcinomas. |
| PCAM | Normal, Tumor | **Task:** Lymph node metastasis detection<br>**Normal:** Healthy lymphoid tissue<br>**Tumor:** Metastatic breast carcinoma. |
| DigestPath | Non-cancerous, Cancerous | **Task:** Digestive-system cancer detection<br>**Non-cancerous:** Benign tissue<br>**Cancerous:** Malignant epithelial tissue. |
| **Molecular Status Prediction** | | |
| Kather-MSI-STAD | MSS, MSI | **Task:** MSI prediction in gastric cancer<br>**MSI:** Deficient DNA mismatch repair (dMMR)<br>**MSS:** Intact mismatch repair. |
| Kather-MSI-CRC | MSS, MSI | **Task:** MSI prediction in colorectal cancer<br>**MSI:** Associated with immunotherapy response<br>**MSS:** Microsatellite stable tumors. |
| **Immune / TIL Assessment** | | |
| CCRCC-Lymphocyte | Blood, Lymphocyte, Tumor | **Task:** Immune composition analysis<br>**Blood:** Blood-rich regions<br>**Lymphocyte:** Immune-cell infiltrates<br>**Tumor:** Clear cell renal carcinoma. |
| TCGA-TILs | Negative, Positive | **Task:** Tumor-infiltrating lymphocyte (TIL) detection<br>**Positive:** Detectable immune infiltration<br>**Negative:** Minimal or absent TILs. |
| **Tissue Typing** | | |
| WSSS4LUAD | Normal, Stroma, Tumor | **Task:** Lung tissue segmentation<br>**Normal:** Pulmonary parenchyma<br>**Stroma:** Connective tissue<br>**Tumor:** Malignant epithelium. |
| CHAOYANG | Adenocarcinoma, Adenoma, Serrated, Normal | **Task:** Colorectal tissue classification<br>**Adenoma/Serrated:** Premalignant lesions<br>**Adenocarcinoma:** Malignant tissue<br>**Normal:** Healthy mucosa. |
| NCT-CRC-HE-100K | ADI, BACK, DEB, LYM, MUC, MUS, NORM, STR, TUM | **Task:** Nine-class colorectal tissue recognition<br>**Classes:** Adipose, background, debris, lymphocytes, mucus, muscle, normal mucosa, stroma, and tumor epithelium. |
| NCT-CRC-VAL-HE-7K | ADI, BACK, DEB, LYM, MUC, MUS, NORM, STR, TUM | **Task:** Independent validation cohort<br>**Classes:** Same nine tissue categories as NCT-CRC-HE-100K. |
| CCRCC-Tissue | Empty, Cancer, Normal, Other, Stroma, Blood | **Task:** Renal tissue classification<br>**Classes:** Background, tumor, normal kidney, stromal, blood, and miscellaneous tissue. |
| **Tumor Subtyping / Grading** | | |
| MHIST | Hyperplastic Polyp (HP), Sessile Serrated Adenoma (SSA) | **Task:** Colorectal polyp classification<br>**HP:** Benign hyperplastic polyp<br>**SSA:** Premalignant serrated lesion. |
| SICAPv2 | Normal, Gleason Grade 3 (GG3), Gleason Grade 4 (GG4), Gleason Grade 5 (GG5) | **Task:** Prostate cancer grading<br>**GG3--GG5:** Increasing Gleason grade and tumor aggressiveness<br>**Normal:** Non-neoplastic prostate tissue. |
\n\n## 🛠️ Usage

### Prerequisites

1. **Configure paths** in `config.py`:
   - `FEAT`: Root directory containing pre-extracted patch features (one HDF5 file per encoder per dataset).
   - `META`: Root directory containing raw patch images and metadata CSVs (needed for invariance re-embedding).

2. **Feature directory layout** — each dataset folder must contain `features_<encoder>.h5` files:
   ```text
   PATCH_Features/
   ├── MHIST/
   │   ├── features_uni_v1.h5
   │   ├── features_uni_v2.h5
   │   ├── features_virchow.h5
   │   └── ...
   ├── CHAOYANG/
   │   └── ...
   └── ...
   ```

---

### Step 1 — Downstream Oracle (CPU)
Compute the labeled ground truth via patient-grouped linear probe and consensus baseline:
```bash
python main.py linear_probe_oracle
```

### Step 2 — Rotation Invariance (GPU)
Apply dihedral rotations (90°, 180°, 270°) to patches, re-embed through each frozen encoder, and measure neighborhood preservation (`retention@10`). Run once **per encoder**:
```bash
# Single encoder
python main.py invariance --encoder uni_v2 --save_emb

# All 22 encoders (loop)
for enc in uni_v1 uni_v2 virchow virchow2 gigapath hoptimus0 hoptimus1 \
           phikon phikon_v2 hibou_l gpfm h0-mini midnight12k openmidnight \
           kaiko-vitb8 kaiko-vitb16 kaiko-vits8 kaiko-vits16 kaiko-vitl14 \
           lunit-vits8 genbio-pathfm ctranspath \
           resnet50 gemma4-e4b gemma4-26b; do
    python main.py invariance --encoder "$enc" --n 4000 --bs 128
done
```

### Step 3 — Aggregate Invariance (CPU)
Aggregate the per-encoder invariance results from Step 2:
```bash
python main.py analyze
```

### Step 4 — Combined Metric (CPU)
Compute effective rank, vMF concentration parameters, and the combined INVEX score with bootstrap confidence intervals:
```bash
python main.py probabilistic
```

### Step 5 — kNN Oracle (CPU)
Compute the kNN-based downstream oracle as a secondary validation target:
```bash
python main.py knn_probe_oracle
```

### Step 6 — Generate Figures & Tables (CPU)
```bash
make all         # runs everything below in order

make metrics     # rebuild results/encoder_metrics.csv (master per-encoder table)
make figures     # hero scatter, leaderboard, top-k/regret, mechanism, baselines
make tables      # ablation table + dataset/encoder reference CSVs
make sensitivity # parameter sweeps (α-weight, angles, k/N/seed, measure, data-efficiency)
```

---

## 🔬 Methodology

INVEX implements a multi-stage evaluation pipeline:

1. **Invariance (GPU)**: For each encoder, apply dihedral rotations (90°, 180°, 270°) to patches, re-embed through the frozen encoder, and measure how well the neighborhood structure is preserved (`retention@10`). A good encoder maps rotated tissue to the same region of embedding space.

2. **Expressiveness (CPU)**: Compute effective rank and uniformity of the clean embedding cloud. A good encoder uses many dimensions — distinct biology lands in distinct parts of the embedding space.

3. **Combined Score**: Model directions with von Mises–Fisher (vMF) distributions on the unit hypersphere. The quality likelihood-ratio $Q_{\text{vMF}} = \log \kappa_{\text{nuis}} - \log \kappa_{\text{bio}}$ captures both invariance (tight clustering under rotation) and expressiveness (diffuse spread across biology). The final INVEX score is $z(\text{retention}) + z(\text{effrank})$.

4. **Validation (CPU)**: Patient-grouped linear probe and kNN oracles provide the downstream ground truth. INVEX's label-free ranking is evaluated via Spearman/Kendall rank correlation against these oracles.

---

## 🙏 Acknowledgements

This project builds upon the following open-source tools from the [Mahmood Lab](https://faisal.ai/):
- [TRIDENT](https://github.com/mahmoodlab/TRIDENT) — Scalable whole-slide image processing and feature extraction toolkit.
- [Patho-Bench](https://github.com/mahmoodlab/Patho-Bench) — Standardized benchmarking library for pathology foundation models.

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.
