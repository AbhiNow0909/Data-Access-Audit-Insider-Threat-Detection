"""Layer 4 — Anomaly scoring engine: composite 0-100 risk score per event.

5 dimensions over real columns: (1) time, (2) action x sensitivity,
(3) unauthorized system access, (4) stale/inactive account, (5) IP & privilege.
See CLAUDE.md for the exact point matrices.

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
