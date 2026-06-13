"""Layer 5 — LLM reasoning: Gemini-generated incident narratives.

All Gemini calls live here and nowhere else. Key is loaded from .env.

Placeholder scaffold (Step 1). Implemented in Step 6.
"""
from __future__ import annotations

import pandas as pd


def generate_narrative(event: pd.Series, baseline: dict, user_profile: dict) -> dict:
    """Return parsed JSON narrative (severity, confidence, narrative, actions)."""
    raise NotImplementedError


def narrate_all_incidents(flagged_df: pd.DataFrame, baselines: dict, profiles: pd.DataFrame) -> pd.DataFrame:
    """Add narrative columns for all flagged incidents."""
    raise NotImplementedError
