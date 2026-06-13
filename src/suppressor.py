"""Layer 4b — False-positive suppression.

Operates on scored events (enriched row + dim1..dim5 + risk_score + severity) and
applies five business-context rules that either zero out a specific dimension
(then the composite score and severity are recomputed) or adjust severity:

  1. Month-end finance close  → downgrade severity one level
  2. Admin works nights       → suppress Dim 1 (time)
  3. New hire (<3 mo tenure)  → suppress Dim 3 (unfamiliar systems)
  4. Inactive account         → ESCALATE to CRITICAL (never suppressed)
  5. Failed access on low/med → suppress the Dim 2 "failed" bonus only

Each rule encodes a documented edge case from the problem statement so analysts
are not buried in predictable false positives. Importable with zero side effects.
Run inline tests with: ``python -m src.suppressor``.
"""
from __future__ import annotations

import pandas as pd

import config
from src.detector import score_action_sensitivity, severity_from_score

_SEVERITY_ORDER = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
_DIM_COLS = [
    "dim1_time", "dim2_action_sensitivity", "dim3_resource",
    "dim4_stale", "dim5_privilege",
]


def _downgrade(severity: str) -> str:
    """Return the severity one band below ``severity`` (floored at LOW)."""
    idx = _SEVERITY_ORDER.index(severity) if severity in _SEVERITY_ORDER else 0
    return _SEVERITY_ORDER[max(0, idx - 1)]


def _is_inactive(value: object) -> bool:
    """True when an is_active field represents a disabled account."""
    return value is False or str(value).strip().lower() == "false"


def _day_of_month(value: object) -> int:
    """Day-of-month from a timestamp that may be a Timestamp or a string."""
    return pd.Timestamp(value).day


def suppress(row: pd.Series) -> dict:
    """Apply all suppression rules to one scored event; return the adjustments."""
    dims = {col: int(row[col]) for col in _DIM_COLS}
    reasons: list[str] = []
    suppressed = False

    # Rule 2 — admins legitimately work odd hours: drop the time penalty.
    if row[config.COL_PRIVILEGE] == "admin" and row[config.COL_TIME_CLASS] == "night":
        if dims["dim1_time"]:
            dims["dim1_time"] = 0
            suppressed = True
            reasons.append("Admin works nights (Dim1 time suppressed)")

    # Rule 3 — new hires explore unfamiliar systems: drop the resource penalty.
    if float(row.get("tenure_months", 99.0)) < 3:
        if dims["dim3_resource"]:
            dims["dim3_resource"] = 0
            suppressed = True
            reasons.append("New hire <3mo (Dim3 resource suppressed)")

    # Rule 5 — a failed read of non-sensitive data is low signal: drop the +5.
    if row[config.COL_STATUS] == "failure" and row[config.COL_SENSITIVITY] in ("low", "medium"):
        no_bonus = score_action_sensitivity(pd.Series({**row.to_dict(), config.COL_STATUS: "success"}))
        if no_bonus < dims["dim2_action_sensitivity"]:
            dims["dim2_action_sensitivity"] = no_bonus
            suppressed = True
            reasons.append("Failed access on non-sensitive resource (Dim2 failed-bonus suppressed)")

    adjusted_score = int(min(sum(dims.values()), 100))
    adjusted_severity = severity_from_score(adjusted_score)

    # Rule 1 — Finance month-end close is expected heavy access: downgrade.
    if (row[config.COL_DEPARTMENT] in config.FINANCE_DEPARTMENTS
            and _day_of_month(row[config.COL_TIMESTAMP]) >= 28):
        lowered = _downgrade(adjusted_severity)
        if lowered != adjusted_severity:
            adjusted_severity = lowered
            suppressed = True
            reasons.append("Month-end Finance close (severity downgraded)")

    # Rule 4 — a disabled account doing anything is always critical. Wins outright.
    if _is_inactive(row.get(config.COL_IS_ACTIVE)):
        adjusted_severity = "CRITICAL"
        reasons.append("Inactive account — escalated to CRITICAL")

    return {
        "suppressed": suppressed,
        "suppression_reason": "; ".join(reasons),
        "adjusted_risk_score": adjusted_score,
        "adjusted_severity": adjusted_severity,
    }


def apply_suppression(scored_df: pd.DataFrame, profiles: pd.DataFrame | None = None) -> pd.DataFrame:
    """Add suppressed / suppression_reason / adjusted_risk_score / adjusted_severity columns.

    ``profiles`` is unused — profile fields are already merged into ``scored_df``
    by the ingestor; the parameter is kept for pipeline-signature consistency.
    """
    records = [suppress(row) for _, row in scored_df.iterrows()]
    adjustments = pd.DataFrame(records, index=scored_df.index)
    return pd.concat([scored_df, adjustments], axis=1)


# --------------------------------------------------------------------------
# Inline unit tests — one hardcoded example per rule. Run: python -m src.suppressor
# --------------------------------------------------------------------------
def _base_row(**overrides) -> pd.Series:
    """A benign business-hours scored event; override fields per test."""
    row = {
        config.COL_TIMESTAMP: pd.Timestamp("2026-04-15", tz="UTC"),
        config.COL_DEPARTMENT: "Engineering",
        config.COL_PRIVILEGE: "user",
        config.COL_TIME_CLASS: "business_hours",
        config.COL_STATUS: "success",
        config.COL_SENSITIVITY: "high",
        config.COL_ACTION: "login",
        config.COL_RESOURCE: "PROD_DB",
        "tenure_months": 24.0,
        config.COL_IS_ACTIVE: True,
        "dim1_time": 0, "dim2_action_sensitivity": 0, "dim3_resource": 0,
        "dim4_stale": 0, "dim5_privilege": 0,
    }
    row.update(overrides)
    return pd.Series(row)


def _run_tests() -> None:
    """Assert each rule fires correctly on a crafted example; print PASS/FAIL."""
    cases = []

    r = suppress(_base_row(**{config.COL_PRIVILEGE: "admin", config.COL_TIME_CLASS: "night", "dim1_time": 20}))
    cases.append(("Rule 2 admin-night suppresses Dim1",
                  r["adjusted_risk_score"] == 0 and r["suppressed"]))

    r = suppress(_base_row(**{"tenure_months": 1.0, "dim3_resource": 25}))
    cases.append(("Rule 3 new-hire suppresses Dim3",
                  r["adjusted_risk_score"] == 0 and r["suppressed"]))

    # export_data on low sensitivity = base 5, +5 failed bonus = 10; bonus removed -> 5
    r = suppress(_base_row(**{config.COL_STATUS: "failure", config.COL_SENSITIVITY: "low",
                              config.COL_ACTION: "export_data", "dim2_action_sensitivity": 10}))
    cases.append(("Rule 5 failed low-sens drops Dim2 bonus (10->5)",
                  r["adjusted_risk_score"] == 5 and r["suppressed"]))

    # Finance month-end: 25+25+15 = 65 (HIGH) -> downgraded to MEDIUM
    r = suppress(_base_row(**{config.COL_DEPARTMENT: "Finance",
                              config.COL_TIMESTAMP: pd.Timestamp("2026-04-29", tz="UTC"),
                              "dim1_time": 15, "dim2_action_sensitivity": 25, "dim3_resource": 25}))
    cases.append(("Rule 1 month-end Finance downgrades HIGH->MEDIUM",
                  r["adjusted_severity"] == "MEDIUM" and r["suppressed"]))

    r = suppress(_base_row(**{config.COL_IS_ACTIVE: False, "dim4_stale": 15}))
    cases.append(("Rule 4 inactive escalates to CRITICAL",
                  r["adjusted_severity"] == "CRITICAL"))

    r = suppress(_base_row(**{"dim2_action_sensitivity": 8}))
    cases.append(("No-op: benign event is not suppressed",
                  not r["suppressed"] and r["adjusted_risk_score"] == 8))

    ok = True
    for name, passed in cases:
        print(f"  [{'PASS' if passed else 'FAIL'}] {name}")
        ok = ok and passed
    print(f"\n{'ALL PASS' if ok else 'SOME FAILED'}")


if __name__ == "__main__":
    _run_tests()
