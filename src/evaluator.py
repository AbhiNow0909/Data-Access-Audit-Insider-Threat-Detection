"""Layer 6 — Evaluation: Precision / Recall / F1 against ground-truth labels.

NOTE: sample_data ships no label files. Until labels are provided, evaluation
runs against a transparent heuristic weak-label set (documented in Step 7) so
metrics are reproducible; swap in real labels via config when available.

Placeholder scaffold (Step 1). Implemented in Step 7.
"""
from __future__ import annotations

import pandas as pd


def calculate_metrics(predictions_df: pd.DataFrame, labels_df: pd.DataFrame) -> dict:
    """Return dict with precision, recall, f1."""
    raise NotImplementedError
