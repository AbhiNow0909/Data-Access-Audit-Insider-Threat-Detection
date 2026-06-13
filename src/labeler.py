"""Tier-2 — Rule-derived ground-truth labeler.

The organizer shipped no label files, so this module derives weak ground-truth
labels from domain rules over the raw columns. These labels are the yardstick the
detector is measured against in src/evaluator.py.

DESIGN — why this is not circular with the detector
----------------------------------------------------
The detector produces an *additive* 0-100 score and flags events at a single
threshold. This labeler instead asserts, categorically, that an event matches one
of a small set of high-confidence insider-threat ARCHETYPES that a human auditor
would independently call suspicious. The two are intentionally built differently:
  - the labeler requires specific, named combinations (e.g. off-hours export of
    sensitive data) rather than a weighted sum crossing a cutoff;
  - it keys on sensitivity = high/medium gates, not per-dimension point values.
They correlate (both encode the same domain reality) but are not identical, so
Precision/Recall/F1 between them is meaningful: a detector flag that matches no
archetype is a false positive; an archetype the detector scores < 50 is a miss.

LABELING ARCHETYPES (in priority order)
  CRITICAL  OFFHOURS_SENSITIVE_EXPORT       export of high/med data at night
  HIGH      OFFHOURS_SENSITIVE_EXPORT       export of high/med data on weekend/unusual
  HIGH      CROSS_DEPARTMENT_SENSITIVE      high-sensitivity resource accessed by a
                                            department that does not own it
  HIGH      PRIVILEGED_NIGHT_ADMIN_OP       admin/power-user admin_operation on
                                            high/med sensitivity at night
  MEDIUM    STALE_ACCOUNT_SENSITIVE         dormant account (days_inactive > 45)
                                            touching high/med sensitivity
  MEDIUM    FAILED_SENSITIVE_ACCESS         failed access attempt on high sensitivity
  (else)    not an anomaly

Importable with zero side effects.
"""
from __future__ import annotations

import pandas as pd

import config

# A dormant-but-active account beyond this many days is treated as stale.
LABEL_STALE_DAYS = 45
_OFF_HOURS = {"night", "unusual_hours", "weekend"}
_ELEVATED = {"admin", "power-user"}


def _anomaly(anomaly_type: str, severity: str) -> dict:
    """Build a positive label record."""
    return {"is_anomaly": True, "anomaly_type": anomaly_type, "derived_severity": severity}


_NORMAL = {"is_anomaly": False, "anomaly_type": None, "derived_severity": "NONE"}


def derive_label(row: pd.Series, profile: pd.Series | None = None) -> dict:
    """Return {is_anomaly, anomaly_type, derived_severity} for one enriched event.

    ``profile`` is accepted for signature symmetry but unused — the enriched row
    already carries the profile columns.
    """
    action = row[config.COL_ACTION]
    sens = row[config.COL_SENSITIVITY]
    tc = row[config.COL_TIME_CLASS]
    status = row[config.COL_STATUS]
    dept = row[config.COL_DEPARTMENT]
    priv = row[config.COL_PRIVILEGE]
    days_inactive = int(row[config.COL_DAYS_INACTIVE]) if pd.notna(row.get(config.COL_DAYS_INACTIVE)) else 0
    sensitive = sens in ("high", "medium")

    # 1) Off-hours export of sensitive data = exfiltration signature.
    if action == "export_data" and sensitive:
        if tc == "night":
            return _anomaly("OFFHOURS_SENSITIVE_EXPORT", "CRITICAL")
        if tc in ("unusual_hours", "weekend"):
            return _anomaly("OFFHOURS_SENSITIVE_EXPORT", "HIGH")

    # 2) Cross-department access to a high-sensitivity owned resource.
    owners = config.RESOURCE_OWNER_DEPARTMENTS.get(row[config.COL_RESOURCE])
    if owners is not None and dept not in owners and sens == "high":
        return _anomaly("CROSS_DEPARTMENT_SENSITIVE", "HIGH")

    # 3) Elevated privilege running admin operations on sensitive data at night.
    if priv in _ELEVATED and action == "admin_operation" and tc == "night" and sensitive:
        return _anomaly("PRIVILEGED_NIGHT_ADMIN_OP", "HIGH")

    # 4) Dormant account touching sensitive data.
    if days_inactive > LABEL_STALE_DAYS and sensitive:
        return _anomaly("STALE_ACCOUNT_SENSITIVE", "MEDIUM")

    # 5) Failed attempt against a high-sensitivity resource (probing).
    if status == "failure" and sens == "high":
        return _anomaly("FAILED_SENSITIVE_ACCESS", "MEDIUM")

    return dict(_NORMAL)


def label_all_events(df: pd.DataFrame, profiles: pd.DataFrame | None = None) -> pd.DataFrame:
    """Derive labels for every event, write config.LABELS_CSV, return labeled frame.

    The returned frame shares ``df``'s index so the evaluator can align labels to
    predictions positionally. ``profiles`` is unused (enriched row carries them).
    """
    labels = pd.DataFrame([derive_label(row) for _, row in df.iterrows()], index=df.index)
    out = pd.concat([df, labels], axis=1)

    config.DATA_OUTPUT.mkdir(parents=True, exist_ok=True)
    id_cols = [config.COL_TIMESTAMP, config.COL_USER_ID, config.COL_USERNAME,
               config.COL_ACTION, config.COL_RESOURCE, config.COL_SENSITIVITY]
    export = out[id_cols + ["is_anomaly", "anomaly_type", "derived_severity"]].copy()
    export.insert(0, "event_idx", out.index)
    export.to_csv(config.LABELS_CSV, index=False)
    return out


if __name__ == "__main__":  # quick self-check: python -m src.labeler
    from src.ingestor import load_access_logs, load_user_profiles, merge_logs_with_profiles

    profiles = load_user_profiles()
    enriched = merge_logs_with_profiles(load_access_logs(), profiles)
    labeled = label_all_events(enriched, profiles)
    n = len(labeled)
    pos = int(labeled["is_anomaly"].sum())
    print(f"events labeled    : {n}")
    print(f"anomalies         : {pos} ({pos / n:.1%})")
    print("by type           :", labeled.loc[labeled.is_anomaly, "anomaly_type"].value_counts().to_dict())
    print("by severity       :", labeled.loc[labeled.is_anomaly, "derived_severity"].value_counts().to_dict())
    print(f"written to        : {config.LABELS_CSV.relative_to(config.ROOT)}")
