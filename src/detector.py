"""Layer 4 — Anomaly scoring engine: composite 0-100 risk score per event.

Operates on the enriched dataframe from src.ingestor (each row already carries
the user's profile columns), plus the per-user baselines from src.baseline.

Five dimensions, adapted to the real data (see docs/architecture.md):
  Dim 1  Time deviation .............. max 20  (behavioral: discounted if habitual)
  Dim 2  Action x Sensitivity ....... max 25
  Dim 3  Inappropriate resource ..... max 25  (cross-department + grant violation)
  Dim 4  Stale / inactive account ... max 15
  Dim 5  Privilege x off-hours ...... max 15  (replaces dead IP-novelty signal)
Composite = sum, clipped to 0-100 (int). Importable with zero side effects.
"""
from __future__ import annotations

import pandas as pd

import config

# --- Dim 1: time -----------------------------------------------------------
_TIME_POINTS = {"business_hours": 0, "unusual_hours": 8, "weekend": 12, "night": 20}


def _is_habitual_time(baseline: dict | None, time_class: str) -> bool:
    """True if the user has this time_classification at least twice in their history.

    Requires >= 2 (not just this event) so a single off-hours event is not
    self-excused; lets genuine night-workers avoid a time penalty.
    """
    if not baseline:
        return False
    return baseline.get("typical_time_classifications", {}).get(time_class, 0) >= 2


def score_time(row: pd.Series, baseline: dict | None = None) -> int:
    """Dim 1: off-hours risk from time_classification, halved if habitual for the user."""
    points = _TIME_POINTS.get(row[config.COL_TIME_CLASS], 0)
    if points and _is_habitual_time(baseline, row[config.COL_TIME_CLASS]):
        points //= 2
    return points


# --- Dim 2: action x sensitivity ------------------------------------------
# Action classes map the real actions onto the CLAUDE.md risk rows.
_ACTION_CLASS = {
    "login": "read", "sql_query": "read", "api_call": "read", "file_access": "read",
    "admin_operation": "admin", "export_data": "export",
}
_ACTION_SENS_POINTS = {
    "read":   {"low": 0, "medium": 2, "high": 8,  "restricted": 15},
    "admin":  {"low": 3, "medium": 8, "high": 18, "restricted": 23},
    "export": {"low": 5, "medium": 10, "high": 20, "restricted": 25},
}
_FAILED_BONUS = 5


def score_action_sensitivity(row: pd.Series) -> int:
    """Dim 2: risk from action class x resource sensitivity, +5 if the access failed."""
    cls = _ACTION_CLASS.get(row[config.COL_ACTION], "read")
    sens = row[config.COL_SENSITIVITY]
    points = _ACTION_SENS_POINTS[cls].get(sens, 0)
    if row[config.COL_STATUS] == "failure":
        points += _FAILED_BONUS
    return min(points, 25)


# --- Dim 3: inappropriate resource access ---------------------------------
_SENS_CROSS_POINTS = {"low": 8, "medium": 15, "high": 25, "restricted": 25}
_SENS_GRANT_POINTS = {"low": 6, "medium": 12, "high": 25, "restricted": 25}


def score_system_access(row: pd.Series) -> int:
    """Dim 3: cross-department access to a sensitive resource, or a grant violation."""
    resource = row[config.COL_RESOURCE]
    sens = row[config.COL_SENSITIVITY]
    points = 0

    owners = config.RESOURCE_OWNER_DEPARTMENTS.get(resource)
    if owners is not None and row[config.COL_DEPARTMENT] not in owners:
        points = _SENS_CROSS_POINTS.get(sens, 0)

    # Valid grant check only for resources whose names exist in the grant vocab.
    if resource in config.GRANT_CHECKABLE_RESOURCES:
        grants = row.get("systems_access_list", []) or []
        if resource not in grants:
            points = max(points, _SENS_GRANT_POINTS.get(sens, 0))

    return min(points, 25)


# --- Dim 4: stale / inactive account --------------------------------------
def score_stale_account(row: pd.Series) -> int:
    """Dim 4: risk from account inactivity / disabled status."""
    if row.get(config.COL_IS_ACTIVE) is False or row.get(config.COL_IS_ACTIVE) == "False":
        return 15
    days = row.get(config.COL_DAYS_INACTIVE)
    days = int(days) if pd.notna(days) else 0
    if days > 90:
        return 12
    if days > 30:
        return 8
    if days > 7:
        return 4
    return 0


# --- Dim 5: privilege x off-hours -----------------------------------------
_ELEVATED = {"admin", "power-user"}


def score_ip_privilege(row: pd.Series) -> int:
    """Dim 5: elevated privilege operating at off-hours (IP-novelty is uninformative here)."""
    if row[config.COL_PRIVILEGE] not in _ELEVATED:
        return 0
    tc = row[config.COL_TIME_CLASS]
    if tc == "night":
        return 15
    if tc in ("unusual_hours", "weekend"):
        return 8
    return 0


# --- Composite -------------------------------------------------------------
def severity_from_score(score: int) -> str:
    """Map a 0-100 risk score to a severity band."""
    for threshold, label in config.SEVERITY_BANDS:
        if score >= threshold:
            return label
    return "LOW"


def _dimension_scores(row: pd.Series, baseline: dict | None) -> dict[str, int]:
    """Compute all five dimension scores for one event."""
    return {
        "dim1_time": score_time(row, baseline),
        "dim2_action_sensitivity": score_action_sensitivity(row),
        "dim3_resource": score_system_access(row),
        "dim4_stale": score_stale_account(row),
        "dim5_privilege": score_ip_privilege(row),
    }


def build_anomaly_signals(row: pd.Series, dims: dict[str, int]) -> list[str]:
    """Human-readable signal strings for each dimension that fired (score > 0)."""
    signals: list[str] = []
    if dims["dim1_time"]:
        signals.append(f"Off-hours access ({row[config.COL_TIME_CLASS]})")
    if dims["dim2_action_sensitivity"]:
        fail = " failed" if row[config.COL_STATUS] == "failure" else ""
        signals.append(
            f"{row[config.COL_ACTION]} on {row[config.COL_SENSITIVITY]}-sensitivity "
            f"{row[config.COL_RESOURCE]}{fail}")
    if dims["dim3_resource"]:
        signals.append(
            f"Cross-department / ungranted access to {row[config.COL_RESOURCE]} "
            f"by {row[config.COL_DEPARTMENT]}")
    if dims["dim4_stale"]:
        signals.append(f"Stale account (days_inactive={row.get(config.COL_DAYS_INACTIVE)})")
    if dims["dim5_privilege"]:
        signals.append(
            f"Elevated privilege ({row[config.COL_PRIVILEGE]}) at "
            f"{row[config.COL_TIME_CLASS]}")
    return signals


def compute_risk_score(row: pd.Series, baseline: dict | None = None) -> tuple[int, list[str]]:
    """Composite integer risk score 0-100 plus the list of anomaly signals."""
    dims = _dimension_scores(row, baseline)
    score = int(min(sum(dims.values()), 100))
    return score, build_anomaly_signals(row, dims)


def score_all_events(
    df: pd.DataFrame,
    baselines: dict[str, dict],
    write: bool = True,
) -> pd.DataFrame:
    """Score every event; add dim1..dim5, risk_score, severity, anomaly_signals.

    ``df`` is the enriched frame from src.ingestor. Writes config.SCORED_CSV when
    ``write`` is True (creating data/output/ if needed).
    """
    out = df.copy()
    dim_rows, scores, signal_strs = [], [], []
    for _, row in out.iterrows():
        baseline = baselines.get(row[config.COL_USER_ID])
        dims = _dimension_scores(row, baseline)
        score = int(min(sum(dims.values()), 100))
        dim_rows.append(dims)
        scores.append(score)
        signal_strs.append("; ".join(build_anomaly_signals(row, dims)))

    dims_df = pd.DataFrame(dim_rows, index=out.index)
    out = pd.concat([out, dims_df], axis=1)
    out["risk_score"] = scores
    out["severity"] = [severity_from_score(s) for s in scores]
    out["anomaly_signals"] = signal_strs

    if write:
        config.DATA_OUTPUT.mkdir(parents=True, exist_ok=True)
        out.to_csv(config.SCORED_CSV, index=False)
    return out


if __name__ == "__main__":  # quick self-check: python -m src.detector
    from src.ingestor import load_access_logs, load_user_profiles, merge_logs_with_profiles
    from src.baseline import build_all_baselines

    profiles = load_user_profiles()
    enriched = merge_logs_with_profiles(load_access_logs(), profiles)
    baselines = build_all_baselines(enriched, profiles)
    scored = score_all_events(enriched, baselines)
    print(f"scored events     : {len(scored)}")
    print(f"risk_score 5-num  : min={scored.risk_score.min()} "
          f"q25={int(scored.risk_score.quantile(.25))} "
          f"med={int(scored.risk_score.median())} "
          f"q75={int(scored.risk_score.quantile(.75))} max={scored.risk_score.max()}")
    print("severity counts   :", scored.severity.value_counts().to_dict())
    print(f"flagged (>= {config.RISK_FLAG_THRESHOLD}): "
          f"{int((scored.risk_score >= config.RISK_FLAG_THRESHOLD).sum())}")
    print(f"written to        : {config.SCORED_CSV.relative_to(config.ROOT)}")
