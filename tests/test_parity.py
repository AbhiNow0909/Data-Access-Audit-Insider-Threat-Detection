"""Parity + performance check for the vectorized pipeline.

Proves the vectorized scorer/suppressor/labeler produce output IDENTICAL to the
row-loop reference oracle on the real data (every output column, all rows), then
benchmarks the speedup. The vectorized path only ships because this passes.

Run:  python -m tests.test_parity      (or: python tests/test_parity.py)
"""
from __future__ import annotations

import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd  # noqa: E402

from src.ingestor import load_access_logs, load_user_profiles, merge_logs_with_profiles  # noqa: E402
from src.baseline import build_all_baselines  # noqa: E402
from src import detector, suppressor, labeler  # noqa: E402
from src.evaluator import evaluate_against_derived  # noqa: E402

_DETECTOR_COLS = ["dim1_time", "dim2_action_sensitivity", "dim3_resource", "dim4_stale",
                  "dim5_privilege", "risk_score", "severity", "anomaly_signals"]
_SUPPRESSOR_COLS = ["suppressed", "suppression_reason", "adjusted_risk_score", "adjusted_severity"]
_LABELER_COLS = ["is_anomaly", "anomaly_type", "derived_severity"]


def _is_null(v) -> bool:
    return v is None or (isinstance(v, float) and pd.isna(v))


def _first_diff(ref: pd.DataFrame, vec: pd.DataFrame, cols: list[str]):
    """Return (col, row, ref_val, vec_val) of the first mismatch, or None if identical."""
    for c in cols:
        a, b = ref[c].tolist(), vec[c].tolist()
        for i, (x, y) in enumerate(zip(a, b)):
            if _is_null(x) and _is_null(y):
                continue
            if x != y:
                return (c, i, x, y)
    return None


def main() -> int:
    profiles = load_user_profiles()
    enriched = merge_logs_with_profiles(load_access_logs(), profiles)
    baselines = build_all_baselines(enriched, profiles)

    # --- Parity: detector / suppressor / labeler -----------------------------
    det_ref = detector._score_all_events_reference(enriched, baselines)
    det_vec = detector._score_all_events_vectorized(enriched, baselines)
    sup_ref = suppressor._apply_suppression_reference(det_vec)
    sup_vec = suppressor._apply_suppression_vectorized(det_vec)
    lab_ref = labeler._label_frame_reference(enriched)
    lab_vec = labeler._label_frame_vectorized(enriched)

    checks = [
        ("detector", det_ref, det_vec, _DETECTOR_COLS),
        ("suppressor", sup_ref, sup_vec, _SUPPRESSOR_COLS),
        ("labeler", lab_ref, lab_vec, _LABELER_COLS),
    ]
    all_ok = True
    print("PARITY (vectorized vs row-loop reference, all 1,200 rows):")
    for name, ref, vec, cols in checks:
        diff = _first_diff(ref, vec, cols)
        if diff is None:
            print(f"  [PASS] {name:11s} - {len(cols)} columns identical")
        else:
            all_ok = False
            c, i, x, y = diff
            print(f"  [FAIL] {name:11s} - col '{c}' row {i}: ref={x!r} vec={y!r}")

    # --- Metrics identical both ways -----------------------------------------
    m_ref = evaluate_against_derived(sup_ref, lab_ref)
    m_vec = evaluate_against_derived(sup_vec, lab_vec)
    same_metrics = (round(m_ref["precision"], 6), round(m_ref["recall"], 6), round(m_ref["f1"], 6)) == \
                   (round(m_vec["precision"], 6), round(m_vec["recall"], 6), round(m_vec["f1"], 6))
    print(f"\nMETRICS: ref P/R/F1 = {m_ref['precision']:.3f}/{m_ref['recall']:.3f}/{m_ref['f1']:.3f}  "
          f"vec = {m_vec['precision']:.3f}/{m_vec['recall']:.3f}/{m_vec['f1']:.3f}  "
          f"-> {'IDENTICAL' if same_metrics else 'DIFFER'}")
    all_ok = all_ok and same_metrics

    # --- Performance ---------------------------------------------------------
    big = pd.concat([enriched] * 20, ignore_index=True)  # ~24,000 rows
    n = len(big)

    t = time.perf_counter()
    r1 = detector._score_all_events_reference(big, baselines)
    suppressor._apply_suppression_reference(r1)
    labeler._label_frame_reference(big)
    t_ref = time.perf_counter() - t

    t = time.perf_counter()
    v1 = detector._score_all_events_vectorized(big, baselines)
    suppressor._apply_suppression_vectorized(v1)
    labeler._label_frame_vectorized(big)
    t_vec = time.perf_counter() - t

    speedup = t_ref / t_vec if t_vec else float("inf")
    per_event_ms = 1000 * t_vec / n
    print(f"\nPERFORMANCE on {n:,} rows (score+suppress+label):")
    print(f"  reference (row loop): {t_ref:6.2f}s")
    print(f"  vectorized          : {t_vec:6.2f}s   ({speedup:.0f}x faster)")
    print(f"  -> 1,000,000 events extrapolated: {per_event_ms * 1_000_000 / 1000:.1f}s "
          f"(single core, target <120s)")

    print(f"\n{'ALL PARITY CHECKS PASS' if all_ok else 'PARITY FAILED'}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
