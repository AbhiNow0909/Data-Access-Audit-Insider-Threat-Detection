"""FastAPI backend for the insider-threat dashboard.

Runs the full pipeline once on startup (ingest -> baseline -> score -> suppress
-> label -> evaluate -> narrate) and caches the results in memory, then serves
them to the React frontend.

Run:  uvicorn api.main:app --reload   (from the project root)
"""
from __future__ import annotations

import math
import os
from contextlib import asynccontextmanager

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import config
from src.ingestor import load_access_logs, load_user_profiles, merge_logs_with_profiles
from src.baseline import build_all_baselines
from src.detector import score_all_events
from src.suppressor import apply_suppression
from src.labeler import label_all_events
from src.evaluator import evaluate_known_anomalies, evaluate_against_derived, per_severity_metrics
from src.llm_narrator import narrate_flagged_incidents, generate_narrative_safe

# How many top incidents to narrate on startup (caps Gemini calls). Env-tunable.
API_TOP_INCIDENTS = int(os.getenv("API_TOP_INCIDENTS", "50"))

# In-memory cache populated on startup.
STATE: dict = {}

# Columns surfaced in the incident list (slim) vs detail (full superset).
_LIST_COLS = [
    "incident_id", "timestamp", "username", "department", "job_title",
    "privilege_level", "action", "resource", "resource_sensitivity",
    "time_classification", "status", "adjusted_risk_score", "adjusted_severity",
    "anomaly_signals", "llm_severity", "narrative_source",
]
_DETAIL_EXTRA = [
    "source_ip", "dim1_time", "dim2_action_sensitivity", "dim3_resource",
    "dim4_stale", "dim5_privilege", "suppressed", "suppression_reason",
    "llm_confidence", "llm_narrative", "llm_recommended_actions",
    "systems_access_list", "tenure_months", "days_inactive", "is_active",
]


def _jsonify(value):
    """Make a single cell JSON-safe (NaN -> None, Timestamp -> iso string)."""
    if isinstance(value, float) and math.isnan(value):
        return None
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    return value


def _records(df: pd.DataFrame, cols: list[str]) -> list[dict]:
    """Convert selected dataframe columns to a list of JSON-safe dict records."""
    present = [c for c in cols if c in df.columns]
    return [{c: _jsonify(v) for c, v in row.items()} for row in df[present].to_dict("records")]


def _build_state() -> None:
    """Run the pipeline end-to-end and cache everything needed by the endpoints."""
    profiles = load_user_profiles()
    enriched = merge_logs_with_profiles(load_access_logs(), profiles)
    baselines = build_all_baselines(enriched, profiles)

    scored = apply_suppression(score_all_events(enriched, baselines, write=True))
    scored = scored.reset_index(drop=True)
    scored["incident_id"] = scored.index

    labeled = label_all_events(enriched)

    metrics = {
        "tier1_critical": evaluate_known_anomalies(scored, labeled),
        "tier2_derived": evaluate_against_derived(scored, labeled),
        "per_severity": per_severity_metrics(scored, labeled),
        "targets": {"precision": 0.75, "recall": 0.70, "f1": 0.72},
    }
    metrics["targets_met"] = all(
        metrics["tier2_derived"][k] >= v for k, v in metrics["targets"].items())

    flagged = narrate_flagged_incidents(scored, baselines, limit=API_TOP_INCIDENTS, write=True)

    # Per-user risk rollup.
    risk_col = "adjusted_risk_score"
    user_max = scored.groupby(config.COL_USER_ID)[risk_col].max().rename("max_risk_score")
    flagged_counts = (scored[scored[risk_col] >= config.RISK_FLAG_THRESHOLD]
                      .groupby(config.COL_USER_ID).size().rename("flagged_events"))
    users = profiles.merge(user_max, on=config.COL_USER_ID, how="left")
    users = users.merge(flagged_counts, on=config.COL_USER_ID, how="left")
    users["flagged_events"] = users["flagged_events"].fillna(0).astype(int)
    users["max_risk_score"] = users["max_risk_score"].fillna(0).astype(int)

    STATE.update(scored=scored, flagged=flagged, users=users, metrics=metrics,
                 n_events=len(scored), n_flagged=int((scored[risk_col] >= config.RISK_FLAG_THRESHOLD).sum()))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Build the cached pipeline state before the app starts serving."""
    _build_state()
    yield


app = FastAPI(title="Insider Threat Detection API", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    """Pipeline status and record counts."""
    if not STATE:
        return {"status": "starting"}
    return {"status": "ok", "events": STATE["n_events"], "flagged": STATE["n_flagged"],
            "narrated": len(STATE["flagged"]), "targets_met": STATE["metrics"]["targets_met"]}


@app.get("/incidents")
def incidents(limit: int = 50) -> list[dict]:
    """Top flagged incidents (narrated), sorted by risk score descending."""
    flagged = STATE["flagged"].sort_values("adjusted_risk_score", ascending=False).head(limit)
    return _records(flagged, _LIST_COLS)


@app.get("/incidents/{incident_id}")
def incident_detail(incident_id: int) -> dict:
    """Full detail for a single incident, including narrative and per-dimension scores."""
    flagged = STATE["flagged"]
    match = flagged[flagged["incident_id"] == incident_id]
    if match.empty:
        raise HTTPException(status_code=404, detail=f"incident {incident_id} not found among flagged")
    return _records(match, _LIST_COLS + _DETAIL_EXTRA)[0]


@app.get("/users")
def users() -> list[dict]:
    """All user profiles with their max risk score and flagged-event count."""
    cols = [config.COL_USER_ID, config.COL_USERNAME, config.COL_DEPARTMENT,
            config.COL_JOB_TITLE, config.COL_PRIVILEGE, config.COL_DAYS_INACTIVE,
            config.COL_IS_ACTIVE, "max_risk_score", "flagged_events"]
    ordered = STATE["users"].sort_values("max_risk_score", ascending=False)
    return _records(ordered, cols)


@app.get("/metrics")
def metrics() -> dict:
    """Evaluation metrics (Tier 1 critical recall, Tier 2 P/R/F1, per-severity)."""
    return STATE["metrics"]


@app.get("/overview")
def overview() -> dict:
    """Aggregate stats for the dashboard charts (computed over ALL events)."""
    scored = STATE["scored"]
    risk = "adjusted_risk_score"
    thr = config.RISK_FLAG_THRESHOLD
    flagged = scored[scored[risk] >= thr]

    sev_order = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    sev_counts = scored["adjusted_severity"].value_counts().to_dict()
    severity = [{"name": s, "count": int(sev_counts.get(s, 0))} for s in sev_order]

    risk_histogram = []
    for lo in range(0, 90, 10):
        cnt = int(((scored[risk] >= lo) & (scored[risk] < lo + 10)).sum())
        risk_histogram.append({"bin": f"{lo}-{lo + 9}", "count": cnt})

    def counts(col: str, k: int | None = None) -> list[dict]:
        vc = flagged[col].value_counts()
        items = [{"name": str(i), "count": int(c)} for i, c in vc.items()]
        return items[:k] if k else items

    return {
        "total": int(len(scored)),
        "flagged": int(len(flagged)),
        "threshold": thr,
        "severity": severity,
        "risk_histogram": risk_histogram,
        "by_department": counts(config.COL_DEPARTMENT, 10),
        "by_resource": counts(config.COL_RESOURCE),
        "by_time": counts(config.COL_TIME_CLASS),
    }


# --- Interactive ad-hoc scoring -------------------------------------------
class ScoreRequest(BaseModel):
    """One access event + the actor's profile context, scored on demand.

    Defaults make every field optional except the event basics; an unseen user is
    fine (scored conservatively against cohort norms, no personal history)."""
    # Event
    timestamp: str | None = None
    action: str = "export_data"
    resource: str = "Customer_Vault"
    resource_sensitivity: str = "high"
    status: str = "success"
    time_classification: str = "night"
    source_ip: str = "0.0.0.0"
    # Actor / profile context
    user_id: str = "AD-HOC"
    username: str = "ad-hoc.user"
    department: str = "IT"
    job_title: str = "Analyst"
    privilege_level: str = "user"
    systems_access: str = ""
    days_inactive: int = 0
    is_active: bool = True
    tenure_months: float = 24.0


@app.post("/score")
def score_event(req: ScoreRequest) -> dict:
    """Score a single ad-hoc event through the exact production pipeline.

    Returns the same shape the batch system produces: risk_score, severity,
    dimension_scores, anomaly_signals, narrative and recommended_actions.
    """
    try:
        ts = pd.to_datetime(req.timestamp, utc=True) if req.timestamp else pd.Timestamp.now(tz="UTC")
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=400, detail=f"unparseable timestamp: {exc}")

    row = {
        config.COL_TIMESTAMP: ts,
        config.COL_USER_ID: req.user_id,
        config.COL_USERNAME: req.username,
        config.COL_ACTION: req.action,
        config.COL_RESOURCE: req.resource,
        config.COL_SENSITIVITY: req.resource_sensitivity,
        config.COL_STATUS: req.status,
        config.COL_SOURCE_IP: req.source_ip,
        config.COL_TIME_CLASS: req.time_classification,
        config.COL_DEPARTMENT: req.department,
        config.COL_JOB_TITLE: req.job_title,
        config.COL_PRIVILEGE: req.privilege_level,
        config.COL_SYSTEMS_ACCESS: req.systems_access,
        "systems_access_list": [t.strip() for t in req.systems_access.split("|") if t.strip()],
        config.COL_DAYS_INACTIVE: req.days_inactive,
        config.COL_IS_ACTIVE: req.is_active,
        "tenure_months": req.tenure_months,
    }

    # No baseline for an ad-hoc user -> no habitual-time discount (conservative).
    df1 = pd.DataFrame([row])
    scored = apply_suppression(score_all_events(df1, {}, write=False))
    r = scored.iloc[0]
    narrative = generate_narrative_safe(r, None)

    return {
        "risk_score": int(r["adjusted_risk_score"]),
        "severity": r["adjusted_severity"],
        "dimension_scores": {
            "time": int(r["dim1_time"]),
            "action_sensitivity": int(r["dim2_action_sensitivity"]),
            "resource": int(r["dim3_resource"]),
            "stale": int(r["dim4_stale"]),
            "privilege": int(r["dim5_privilege"]),
        },
        "anomaly_signals": [s for s in str(r["anomaly_signals"]).split("; ") if s],
        "narrative": narrative.get("narrative"),
        "narrative_source": narrative.get("narrative_source"),
        "confidence": narrative.get("confidence"),
        "recommended_actions": narrative.get("recommended_actions", []),
        "suppression": r["suppression_reason"] or None,
    }
