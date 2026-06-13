"""Layer 3 — Behavioral baseline engine: per-user statistical profiles.

Baselines are derived from the first BASELINE_WINDOW_DAYS of log activity
(profiles do not ship with avg/typical-hours columns, so we learn them).

Placeholder scaffold (Step 1). Implemented in Step 3.
"""
from __future__ import annotations

import pandas as pd


def build_user_baseline(user_df: pd.DataFrame) -> dict:
    """Build a single user's baseline stats from their training-window events."""
    raise NotImplementedError


def build_all_baselines(df: pd.DataFrame) -> dict:
    """Build baselines for all users, keyed by user_id."""
    raise NotImplementedError
