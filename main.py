#!/usr/bin/env python
"""INVEX CLI entry point.

Usage:
    python main.py <phase> [args...]

Examples:
    python main.py invariance --encoder uni_v2 --save_emb  # rotation-invariance (GPU)
    python main.py analyze                                 # aggregate invariance results
    python main.py probabilistic                           # probabilistic combined metric
    python main.py linear_probe_oracle                         # linear_probe_oracle + downstream oracle
    python main.py knn_probe_oracle                                     # KNN oracle
    python main.py money_plot                              # consensus 'money plot'

Each phase is a module under pipeline/; it is run as __main__ with the remaining
args forwarded, so slurm scripts and interactive runs share one entry point.
"""
import sys, os, runpy

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)          # makes config / utils / pipeline importable from any cwd

PHASES = {
    "money_plot":      "pipeline.money_plot",
    "linear_probe_oracle": "pipeline.linear_probe_oracle",
    "invariance":      "pipeline.invariance",
    "analyze":         "pipeline.analyze",
    "probabilistic":   "pipeline.probabilistic",
    "knn_probe_oracle":             "pipeline.knn_probe_oracle",
}


def _usage(code):
    print("INVEX — usage: python main.py <phase> [args...]\n\nphases:")
    for k, v in PHASES.items():
        print(f"  {k:16s} -> {v}")
    sys.exit(code)


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        _usage(0)
    phase = sys.argv[1]
    if phase not in PHASES:
        print(f"unknown phase: {phase}\n")
        _usage(2)
    sys.argv = [PHASES[phase]] + sys.argv[2:]        # forward remaining args to the phase
    runpy.run_module(PHASES[phase], run_name="__main__")


if __name__ == "__main__":
    main()
