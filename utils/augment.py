"""Pathology nuisance augmentations for the invariance metric (Pillar B1).
Self-contained HED stain jitter (Ruifrok-Johnston deconvolution matrix) + 90deg
rotation + mild blur. Each aug is a pure nuisance a good encoder should be robust to."""
import numpy as np
from PIL import Image, ImageFilter

# Ruifrok & Johnston H&E-DAB stain matrix (rows = H, E, DAB in RGB optical-density space)
RGB_FROM_HED = np.array([[0.65, 0.70, 0.29],
                         [0.07, 0.99, 0.11],
                         [0.27, 0.57, 0.78]], dtype=np.float64)
HED_FROM_RGB = np.linalg.inv(RGB_FROM_HED)


def stain_hed(img, rng, sigma=0.06):
    """Jitter haematoxylin/eosin/DAB concentrations in optical-density space (Tellez-style)."""
    a = np.asarray(img, np.float32) / 255.0
    h, w, _ = a.shape
    a = np.clip(a, 1e-6, 1.0)
    od = -np.log(a).reshape(-1, 3)
    hed = od @ HED_FROM_RGB
    alpha = rng.uniform(1 - sigma, 1 + sigma, 3)     # per-stain scale
    beta = rng.uniform(-sigma, sigma, 3)             # per-stain bias
    hed = hed * alpha + beta
    rgb = np.exp(-(hed @ RGB_FROM_HED)).reshape(h, w, 3)
    return Image.fromarray((np.clip(rgb, 0, 1) * 255).astype("uint8"))


def rotate90(img, rng):
    return img.rotate(int(rng.choice([90, 180, 270])), expand=False)


def blur(img, rng):
    return img.filter(ImageFilter.GaussianBlur(radius=float(rng.uniform(0.7, 1.3))))


AUGS = {"stain_hed": stain_hed, "rotate90": rotate90, "blur": blur}


# ---- EXACT biology-preserving symmetries of tissue (lossless; no canonical orientation) ----
def rot90(img, rng=None):  return img.transpose(Image.ROTATE_90)
def rot180(img, rng=None): return img.transpose(Image.ROTATE_180)
def rot270(img, rng=None): return img.transpose(Image.ROTATE_270)
def hflip(img, rng=None):  return img.transpose(Image.FLIP_LEFT_RIGHT)

# invariance-test set: 4 exact dihedral symmetries (orientation) + stain nuisance.
# All callable as fn(img, rng); the dihedral ops ignore rng (deterministic/exact).
INVARIANCE_TRANSFORMS = {
    "rot90": rot90, "rot180": rot180, "rot270": rot270, "hflip": hflip,
    "stain_hed": stain_hed,
}
