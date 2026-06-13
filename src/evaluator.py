"""Layer 6 — Three-tier evaluation framework.

No organizer labels ship with the data, so evaluation stacks three tiers:
Tier 1 known-anomaly recall, Tier 2 full P/R/F1 vs rule-derived labels
(src/labeler.py), Tier 3 plug-in organizer labels when available.

Placeholder scaffold (Step 1). Implemented in Step 8.
"""
from __future__ import annotations

import pandas as pd


def full_evaluation_report(
    scored_df: pd.DataFrame,
    profiles_df: pd.DataFrame,
    organizer_labels_df: pd.DataFrame | None = None,
) -> dict:
    """Run all available tiers, print a unified report, and return a metrics dict."""
    raise NotImplementedError
