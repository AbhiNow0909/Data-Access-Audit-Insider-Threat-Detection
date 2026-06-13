"""Tier-2 — Rule-derived ground-truth labeler.

Organizer label files are not shipped, so this derives is_anomaly /
anomaly_type / derived_severity per event from domain rules over the real
columns (time_classification, resource_sensitivity, systems_access, action,
status, is_active, days_inactive). Methodology is documented transparently for
judges. Output is written to config.LABELS_CSV.

Placeholder scaffold (Step 1). Implemented in Step 6.
"""
from __future__ import annotations

import pandas as pd


def derive_label(row: pd.Series, profile: dict) -> dict:
    """Return {is_anomaly, anomaly_type, derived_severity} for a single event."""
    raise NotImplementedError


def label_all_events(df: pd.DataFrame, profiles: pd.DataFrame) -> pd.DataFrame:
    """Derive labels for all events and write them to config.LABELS_CSV."""
    raise NotImplementedError
