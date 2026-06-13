"""Layer 2 — Ingestion & normalization: load, merge, and clean the CSVs.

Placeholder scaffold (Step 1). Implemented in Step 2.
"""
from __future__ import annotations

import pandas as pd


def load_access_logs() -> pd.DataFrame:
    """Load data_access_logs.csv with timestamps parsed to UTC."""
    raise NotImplementedError


def load_user_profiles() -> pd.DataFrame:
    """Load user_profiles.csv."""
    raise NotImplementedError


def merge_logs_with_profiles(logs: pd.DataFrame, profiles: pd.DataFrame) -> pd.DataFrame:
    """Left-join access logs with user profiles on user_id."""
    raise NotImplementedError
