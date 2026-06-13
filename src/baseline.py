"""Layer 3 — Behavioral baseline engine.

The dataset is temporally sparse (~12 events per user across the full year), so
a fixed 30-day training window leaves ~64% of users with no baseline. Instead,
each user's baseline is learned from their FULL event history, and a cohort
baseline (grouped by ``privilege_level``) provides a fallback so thin/zero-history
users and admins get sensibly *wider* expected patterns rather than firing every
"new IP / first-time resource" signal.

A baseline dict carries: seen_ips, typical_time_classifications, typical_actions,
typical_resources, typical_sensitivities, tenure_months, privilege_level,
is_admin, event_count, low_confidence. Importable with zero side effects.
"""
from __future__ import annotations

from collections import Counter

import pandas as pd

import config


def _aggregate(events: pd.DataFrame) -> dict:
    """Aggregate a set of events into the raw behavioral stats used by a baseline."""
    return {
        "seen_ips": set(events[config.COL_SOURCE_IP]),
        "typical_time_classifications": Counter(events[config.COL_TIME_CLASS]),
        "typical_actions": Counter(events[config.COL_ACTION]),
        "typical_resources": set(events[config.COL_RESOURCE]),
        "typical_sensitivities": Counter(events[config.COL_SENSITIVITY]),
    }


def build_cohort_baselines(df: pd.DataFrame) -> dict[str, dict]:
    """Build one aggregated baseline per privilege_level cohort, for fallback use."""
    cohorts: dict[str, dict] = {}
    for cohort, group in df.groupby(config.COL_PRIVILEGE):
        agg = _aggregate(group)
        agg["cohort"] = cohort
        agg["event_count"] = len(group)
        cohorts[cohort] = agg
    return cohorts


def build_user_baseline(
    user_events: pd.DataFrame,
    profile_row: pd.Series,
    cohort_baseline: dict | None = None,
) -> dict:
    """Build one user's full-history baseline, widening thin/admin users via cohort."""
    agg = _aggregate(user_events)
    n = len(user_events)
    privilege = profile_row[config.COL_PRIVILEGE]
    is_admin = privilege == "admin"
    low_confidence = n < config.BASELINE_MIN_EVENTS

    # Effective sets start from the user's own history; for thin baselines or
    # admins (legitimately broad access) we union in the cohort's patterns so the
    # detector does not over-fire new-IP / first-time-resource signals.
    seen_ips = set(agg["seen_ips"])
    typical_resources = set(agg["typical_resources"])
    if cohort_baseline is not None and (low_confidence or is_admin):
        seen_ips |= cohort_baseline["seen_ips"]
        typical_resources |= cohort_baseline["typical_resources"]

    return {
        "user_id": profile_row[config.COL_USER_ID],
        "event_count": n,
        "low_confidence": low_confidence,
        "privilege_level": privilege,
        "is_admin": is_admin,
        "cohort": privilege,
        "tenure_months": float(profile_row.get("tenure_months", 0.0)),
        # effective (own + cohort fallback) — what the detector reads
        "seen_ips": seen_ips,
        "typical_resources": typical_resources,
        # user's own history, kept for transparency / EDA
        "seen_ips_own": set(agg["seen_ips"]),
        "typical_resources_own": set(agg["typical_resources"]),
        "typical_time_classifications": agg["typical_time_classifications"],
        "typical_actions": agg["typical_actions"],
        "typical_sensitivities": agg["typical_sensitivities"],
    }


def build_all_baselines(df: pd.DataFrame, profiles: pd.DataFrame) -> dict[str, dict]:
    """Build full-history baselines for every profiled user, keyed by user_id."""
    cohorts = build_cohort_baselines(df)
    grouped = dict(tuple(df.groupby(config.COL_USER_ID)))
    empty = df.iloc[0:0]

    baselines: dict[str, dict] = {}
    for _, profile in profiles.iterrows():
        uid = profile[config.COL_USER_ID]
        events = grouped.get(uid, empty)
        cohort_baseline = cohorts.get(profile[config.COL_PRIVILEGE])
        baselines[uid] = build_user_baseline(events, profile, cohort_baseline)
    return baselines


if __name__ == "__main__":  # quick self-check: python -m src.baseline
    from src.ingestor import load_access_logs, load_user_profiles, merge_logs_with_profiles

    profiles = load_user_profiles()
    enriched = merge_logs_with_profiles(load_access_logs(), profiles)
    baselines = build_all_baselines(enriched, profiles)
    low = sum(b["low_confidence"] for b in baselines.values())
    zero = sum(b["event_count"] == 0 for b in baselines.values())
    sample = next(iter(baselines.values()))
    print(f"baselines built      : {len(baselines)}")
    print(f"low_confidence users : {low}")
    print(f"zero-history users   : {zero}")
    print(f"sample user          : {sample['user_id']} "
          f"(events={sample['event_count']}, ips={len(sample['seen_ips'])}, "
          f"resources={len(sample['typical_resources'])})")
