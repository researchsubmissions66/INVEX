PY ?= python

# Reproduce the paper's figures & tables from the banked results/ artifacts (CPU only).
# The heavy GPU stage (rotated re-embedding, invariance) is assumed already run; see README.

.PHONY: all metrics figures tables sensitivity test clean

all: metrics figures tables sensitivity test

metrics:            ## rebuild results/encoder_metrics.csv (recomputes effective rank)
	$(PY) analysis/build_metrics_table.py

figures: metrics    ## hero scatter, leaderboard, top-k/regret, mechanism, reliability-gating -> figures/
	$(PY) analysis/hero_scatter.py
	$(PY) analysis/leaderboard.py
	$(PY) analysis/topk_regret.py
	$(PY) analysis/mechanism.py
	$(PY) analysis/reliability_gated.py
	$(PY) analysis/baselines_comparison.py

tables: metrics      ## ablation table + dataset/encoder reference CSVs -> docs/
	$(PY) analysis/ablation_table.py
	$(PY) analysis/export_tables.py

sensitivity: metrics ## parameter sweeps: α-weight, operationalization, angles, k/N/seed, measure, data-efficiency
	$(PY) analysis/sensitivity.py           # α-weight + operationalization (instant)
	$(PY) analysis/sensitivity_angles.py    # individual rotation angles (instant)
	$(PY) analysis/sensitivity_metrics.py   # discriminability-measure + data-efficiency (~10 min)
	$(PY) analysis/sensitivity_knn_probe_oracle.py       # k / N / seed on banked embeddings (~15 min)

test:               ## unit tests for the metric primitives
	$(PY) tests/test_metrics.py

clean:
	rm -f figures/*.png
