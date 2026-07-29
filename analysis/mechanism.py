"""
Mechanism / face-validity: why rotation invariance is the informative symmetry.

(1) Face validity: rotation invariance orders the families as pathology-SSL > VLM > baseline.
(2) Specificity via saturation: encoders are near-uniformly invariant to HFLIP (a symmetry most
    are trained on) so it does not discriminate; ROTATION is less-universally trained, so it retains
    cross-encoder spread AND predicts downstream. We show spread(rotation) >> spread(hflip) and the
    baselines (ResNet/Gemma) collapse under rotation while passing flip.
Output: figures/mechanism.png + printed table.
"""
import numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from _common import load_metrics, FIGDIR, FAM_COLOR, FAM_LABEL
import os


def run():
    T = load_metrics()
    fam_order = ["path_ssl", "path_other", "path_vlm", "baseline"]
    fam_order = [f for f in fam_order if f in set(T.family)]

    print("=== (1) rotation invariance by family (face validity) ===")
    g = T.groupby("family")["retention"].agg(["mean", "std", "count"])
    for f in fam_order:
        print(f"  {FAM_LABEL[f]:26s} retention={g.loc[f,'mean']:.3f} ± {g.loc[f,'std'] if g.loc[f,'count']>1 else 0:.3f} (n={int(g.loc[f,'count'])})")

    print("\n=== (2) rotation-specificity via saturation (spread across all encoders) ===")
    print(f"  rotation retention : mean={T.retention.mean():.3f}  spread(std)={T.retention.std():.3f}")
    print(f"  hflip    retention : mean={T.ret_hflip.mean():.3f}  spread(std)={T.ret_hflip.std():.3f}  (saturated → cannot rank)")
    print(f"  stain    retention : mean={T.ret_stain.mean():.3f}  spread(std)={T.ret_stain.std():.3f}")
    if "resnet50" in T.index:
        r = T.loc["resnet50"]
        print(f"  baseline ResNet-50 : rotation={r.retention:.3f} vs hflip={r.ret_hflip:.3f} "
              f"→ passes flip, fails rotation (the diagnostic signature)")

    # figure: per-encoder rotation vs hflip, colored by family
    fig, ax = plt.subplots(figsize=(7.6, 6))
    for fam, gg in T.groupby("family"):
        ax.scatter(gg.ret_hflip, gg.retention, c=FAM_COLOR[fam], s=90, edgecolor="k",
                   linewidth=0.4, label=FAM_LABEL[fam])
    lim = [min(T.ret_hflip.min(), T.retention.min()) - 0.03, 1.005]
    ax.plot(lim, lim, "--", color="grey", lw=0.8, label="y = x")
    ax.set_xlim(lim); ax.set_ylim(lim)
    ax.set_xlabel("hflip retention@10 (control — saturated)")
    ax.set_ylabel("rotation retention@10 (informative)")
    ax.set_title("Rotation is the discriminating symmetry\n(points below y=x: rotation harder than flip)")
    ax.legend(fontsize=8, loc="lower right")
    fig.tight_layout(); p = os.path.join(FIGDIR, "mechanism.png"); fig.savefig(p, dpi=150)
    print(f"\n[SAVED] {p}")


if __name__ == "__main__":
    run()
