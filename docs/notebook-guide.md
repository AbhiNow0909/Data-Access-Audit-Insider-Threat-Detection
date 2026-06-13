# Notebook guide

Two notebooks, both import from `src/` (no logic duplicated):

- `01_eda_and_baseline.ipynb` — data overview, access-pattern distributions,
  per-user baseline visualizations, key findings.
- `02_anomaly_detection_evaluation.ipynb` — run detector, P/R/F1 + per-severity,
  confusion matrix, false-positive / suppression analysis, example incidents,
  scaling notes.

Both must run clean via **Kernel → Restart & Run All** with outputs saved.
