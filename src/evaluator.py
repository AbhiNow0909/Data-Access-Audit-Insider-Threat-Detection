"""Layer 6 - Three-tier evaluation framework.

No organizer labels ship with the data, so evaluation stacks three tiers:
  Tier 1  Critical-anomaly recall - do we catch the clearest threats?
  Tier 2  Full Precision / Recall / F1 vs rule-derived labels (src/labeler.py)
  Tier 3  Plug-in organizer labels, when supplied via config / argument

A "prediction" is ``adjusted_risk_score >= config.RISK_FLAG_THRESHOLD``. Labels
and predictions are aligned positionally (same enriched frame / index).

Importable with zero side effects.
"""
from __future__ import annotations

import pandas as pd
from sklearn.metrics import precision_score, recall_score, f1_score

import config
from src.labeler import label_all_events

_PRED_COL = "adjusted_risk_score"


def _predictions(scored_df: pd.DataFrame) -> pd.Series:
    """Binary anomaly predictions from the (suppression-adjusted) risk score."""
    col = _PRED_COL if _PRED_COL in scored_df.columns else "risk_score"
    return (scored_df[col] >= config.RISK_FLAG_THRESHOLD).astype(int)


def _prf(y_true: pd.Series, y_pred: pd.Series) -> dict:
    """Precision / Recall / F1 plus the confusion-cell counts."""
    yt, yp = y_true.to_numpy(), y_pred.to_numpy()
    tp = int(((yt == 1) & (yp == 1)).sum())
    fp = int(((yt == 0) & (yp == 1)).sum())
    fn = int(((yt == 1) & (yp == 0)).sum())
    tn = int(((yt == 0) & (yp == 0)).sum())
    return {
        "precision": float(precision_score(yt, yp, zero_division=0)),
        "recall": float(recall_score(yt, yp, zero_division=0)),
        "f1": float(f1_score(yt, yp, zero_division=0)),
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "flagged": int(yp.sum()), "n": int(len(yt)),
    }


def evaluate_against_labels(scored_df: pd.DataFrame, labels_df: pd.DataFrame) -> dict:
    """Tier 3 (source-agnostic): P/R/F1 of predictions vs any labels dataframe."""
    return _prf(labels_df["is_anomaly"].astype(int), _predictions(scored_df))


def evaluate_against_derived(scored_df: pd.DataFrame, labels_df: pd.DataFrame) -> dict:
    """Tier 2: full P/R/F1 against the rule-derived labels."""
    return evaluate_against_labels(scored_df, labels_df)


def evaluate_known_anomalies(scored_df: pd.DataFrame, labels_df: pd.DataFrame) -> dict:
    """Tier 1: recall on the clearest threats (CRITICAL-severity derived anomalies).

    The original design named specific access_ids, but the shipped data has no
    such column; the highest-confidence archetype (off-hours sensitive export,
    labeled CRITICAL) is the equivalent "must-catch" set.
    """
    crit = labels_df["derived_severity"] == "CRITICAL"
    pred = _predictions(scored_df)
    n = int(crit.sum())
    caught = int(pred[crit.to_numpy()].sum())
    return {"critical_anomalies": n, "caught": caught,
            "recall": (caught / n) if n else None}


def per_severity_metrics(scored_df: pd.DataFrame, labels_df: pd.DataFrame) -> dict:
    """Recall broken down by the true (derived) severity band."""
    pred = _predictions(scored_df).to_numpy()
    out: dict[str, dict] = {}
    for sev in ("CRITICAL", "HIGH", "MEDIUM"):
        mask = (labels_df["derived_severity"] == sev).to_numpy()
        n = int(mask.sum())
        caught = int(pred[mask].sum())
        out[sev] = {"n": n, "caught": caught, "recall": (caught / n) if n else None}
    return out


def full_evaluation_report(
    scored_df: pd.DataFrame,
    profiles_df: pd.DataFrame | None = None,
    organizer_labels_df: pd.DataFrame | None = None,
) -> dict:
    """Run all available tiers, print a unified report, and return a metrics dict.

    Tier 2 labels are derived from ``scored_df`` (which carries the raw columns).
    Tier 3 runs only if ``organizer_labels_df`` is provided.
    """
    derived = label_all_events(scored_df)

    tier1 = evaluate_known_anomalies(scored_df, derived)
    tier2 = evaluate_against_derived(scored_df, derived)
    by_sev = per_severity_metrics(scored_df, derived)
    tier3 = evaluate_against_labels(scored_df, organizer_labels_df) if organizer_labels_df is not None else None

    targets = {"precision": 0.75, "recall": 0.70, "f1": 0.72}
    ok = all(tier2[k] >= v for k, v in targets.items())

    print("=" * 60)
    print(" INSIDER THREAT DETECTION - EVALUATION REPORT")
    print("=" * 60)
    print(f" Flag threshold: risk_score >= {config.RISK_FLAG_THRESHOLD}")
    print(f" Events: {tier2['n']}   Flagged: {tier2['flagged']}")
    print("-" * 60)
    print(" TIER 1 - Critical-anomaly recall")
    print(f"   caught {tier1['caught']}/{tier1['critical_anomalies']} "
          f"({(tier1['recall'] or 0):.1%})")
    print(" TIER 2 - Derived-label metrics")
    print(f"   Precision {tier2['precision']:.3f}  (target >0.75)")
    print(f"   Recall    {tier2['recall']:.3f}  (target >0.70)")
    print(f"   F1        {tier2['f1']:.3f}  (target >0.72)")
    print(f"   Confusion  TP={tier2['tp']} FP={tier2['fp']} "
          f"FN={tier2['fn']} TN={tier2['tn']}")
    print("   Recall by true severity:")
    for sev, m in by_sev.items():
        rec = f"{m['recall']:.1%}" if m["recall"] is not None else "n/a"
        print(f"     {sev:8s} {m['caught']}/{m['n']} ({rec})")
    if tier3 is not None:
        print(" TIER 3 - Organizer labels")
        print(f"   Precision {tier3['precision']:.3f}  Recall {tier3['recall']:.3f}  "
              f"F1 {tier3['f1']:.3f}")
    print("-" * 60)
    print(f" TARGETS MET: {'YES' if ok else 'NO'}")
    print("=" * 60)

    return {"tier1": tier1, "tier2": tier2, "per_severity": by_sev,
            "tier3": tier3, "targets_met": ok}


if __name__ == "__main__":  # full pipeline + report: python -m src.evaluator
    from src.ingestor import load_access_logs, load_user_profiles, merge_logs_with_profiles
    from src.baseline import build_all_baselines
    from src.detector import score_all_events
    from src.suppressor import apply_suppression

    profiles = load_user_profiles()
    enriched = merge_logs_with_profiles(load_access_logs(), profiles)
    baselines = build_all_baselines(enriched, profiles)
    scored = apply_suppression(score_all_events(enriched, baselines, write=False))
    full_evaluation_report(scored, profiles)
