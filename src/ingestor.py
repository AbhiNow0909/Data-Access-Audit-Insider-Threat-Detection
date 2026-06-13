"""Layer 2 — Ingestion & normalization.

Loads the two read-only organizer CSVs, normalizes timestamps to UTC, parses
the pipe-separated ``systems_access`` grant list into a Python list, derives
``tenure_months`` from ``hire_date``, and left-joins logs to profiles into a
single enriched dataframe used by every downstream layer.

Importable with zero side effects.
"""
from __future__ import annotations

import pandas as pd

import config

# Columns every access-log file must contain (fail fast if the schema drifts).
_REQUIRED_LOG_COLS = [
    config.COL_TIMESTAMP, config.COL_USER_ID, config.COL_USERNAME, config.COL_ACTION,
    config.COL_RESOURCE, config.COL_SENSITIVITY, config.COL_STATUS,
    config.COL_SOURCE_IP, config.COL_TIME_CLASS,
]
_REQUIRED_PROFILE_COLS = [
    config.COL_USER_ID, config.COL_USERNAME, config.COL_DEPARTMENT, config.COL_JOB_TITLE,
    config.COL_PRIVILEGE, config.COL_SYSTEMS_ACCESS, config.COL_LAST_LOGIN,
    config.COL_DAYS_INACTIVE, config.COL_IS_ACTIVE, config.COL_HIRE_DATE,
]

# Reference "now" for tenure: the day after the last observed event, so tenure
# is reproducible and independent of the wall clock when the pipeline is re-run.
_DAYS_PER_MONTH = 30.0


def _validate_columns(df: pd.DataFrame, required: list[str], name: str) -> None:
    """Raise ValueError if any required column is missing from ``df``."""
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"{name} is missing required columns: {missing}")


def load_access_logs() -> pd.DataFrame:
    """Load data_access_logs.csv with timestamps parsed to tz-aware UTC."""
    df = pd.read_csv(config.LOGS_CSV)
    _validate_columns(df, _REQUIRED_LOG_COLS, "data_access_logs.csv")
    # Source timestamps are naive local time; treat as UTC per the ingest rule.
    df[config.COL_TIMESTAMP] = pd.to_datetime(df[config.COL_TIMESTAMP], utc=True)
    return df.sort_values(config.COL_TIMESTAMP).reset_index(drop=True)


def _parse_systems_access(value: object) -> list[str]:
    """Split a pipe-separated grant string into a clean list of system tokens."""
    if not isinstance(value, str) or not value.strip():
        return []
    return [tok.strip() for tok in value.split("|") if tok.strip()]


def load_user_profiles(reference_time: pd.Timestamp | None = None) -> pd.DataFrame:
    """Load user_profiles.csv, parse systems_access to list, derive tenure_months."""
    df = pd.read_csv(config.PROFILES_CSV)
    _validate_columns(df, _REQUIRED_PROFILE_COLS, "user_profiles.csv")

    df[config.COL_HIRE_DATE] = pd.to_datetime(df[config.COL_HIRE_DATE], utc=True)
    df[config.COL_LAST_LOGIN] = pd.to_datetime(df[config.COL_LAST_LOGIN], utc=True)
    df["systems_access_list"] = df[config.COL_SYSTEMS_ACCESS].apply(_parse_systems_access)

    ref = reference_time if reference_time is not None else pd.Timestamp.now(tz="UTC")
    df["tenure_months"] = ((ref - df[config.COL_HIRE_DATE]).dt.days / _DAYS_PER_MONTH).round(1)
    return df


def merge_logs_with_profiles(logs: pd.DataFrame, profiles: pd.DataFrame) -> pd.DataFrame:
    """Left-join logs to profiles on user_id, keeping a single ``username`` column."""
    # username is identical in both files; drop the profile copy to avoid a
    # suffixed duplicate and keep one clean ``username`` for downstream/LLM use.
    profiles_to_join = profiles.drop(columns=[config.COL_USERNAME])
    merged = logs.merge(profiles_to_join, on=config.COL_USER_ID, how="left")
    assert merged.columns.is_unique, "merge produced duplicate columns"
    return merged


def handle_nulls(df: pd.DataFrame) -> pd.DataFrame:
    """Flag rows whose user_id had no matching profile; fill categoricals defensively.

    The shipped data is fully populated, but we stay robust: a ``profile_missing``
    boolean marks unmatched users, and any residual null object cells become the
    literal string ``"unknown"`` so downstream string ops never crash.
    """
    out = df.copy()
    out["profile_missing"] = out[config.COL_DEPARTMENT].isna()
    obj_cols = out.select_dtypes(include="object").columns
    out[obj_cols] = out[obj_cols].fillna("unknown")
    return out


def load_enriched() -> pd.DataFrame:
    """Run the full ingest path and return the enriched, null-handled dataframe."""
    logs = load_access_logs()
    profiles = load_user_profiles()
    return handle_nulls(merge_logs_with_profiles(logs, profiles))


if __name__ == "__main__":  # quick self-check: python -m src.ingestor
    enriched = load_enriched()
    print(f"enriched shape       : {enriched.shape}")
    print(f"columns unique       : {enriched.columns.is_unique}")
    print(f"timestamp tz         : {enriched[config.COL_TIMESTAMP].dt.tz}")
    print(f"unmatched profiles   : {int(enriched['profile_missing'].sum())}")
    print(f"systems_access type  : {type(load_user_profiles()['systems_access_list'].iloc[0]).__name__}")
