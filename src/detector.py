"""Layer 4 — Anomaly scoring engine: composite 0-100 risk score per event.

Scoring dimensions are adapted to the available columns (time, sensitivity,
first-time resource access, action risk, failure/off-hours combos) since the
logs contain no rowcount/destination fields.

Placeholder scaffold (Step 1). Implemented in Step 4.
"""
from __future__ import annotations

import pandas as pd


def compute_risk_score(event: pd.Series, baseline: dict) -> int:
    """Composite integer risk score 0-100 for a single event."""
    raise NotImplementedError


def score_all_events(df: pd.DataFrame, baselines: dict) -> pd.DataFrame:
    """Return df with added risk_score and anomaly_signals columns."""
    raise NotImplementedError
