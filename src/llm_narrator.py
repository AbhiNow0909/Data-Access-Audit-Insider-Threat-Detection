"""Layer 5 — LLM reasoning: Gemini-generated incident narratives.

All Gemini access is isolated here. The API key is read from .env lazily (inside
functions) so the module imports with zero side effects and works even when
google-generativeai is not installed. Every event is run through
``generate_narrative_safe``: it tries Gemini and, on any failure (no key, no
package, quota, bad JSON), falls back to a deterministic rule-based narrative so
the pipeline always yields usable incident write-ups.

Only events with ``risk_score >= config.RISK_FLAG_THRESHOLD`` are narrated.
"""
from __future__ import annotations

import json
import os
import re

import pandas as pd

import config

_PROMPT_TEMPLATE = """You are a cybersecurity analyst reviewing a data access anomaly.
Respond ONLY with the JSON structure below - no preamble, no markdown.

USER:
  Name: {username} | Role: {job_title} | Dept: {department}
  Privilege: {privilege_level}
  Account: active={is_active}, days_inactive={days_inactive}
  Approved systems: {systems_access}
  Tenure: {tenure_months} months

EVENT:
  Time: {timestamp} ({time_classification})
  Action: {action} on {resource}
  Sensitivity: {resource_sensitivity}
  Status: {status}
  Source IP: {source_ip} ({ip_note})

DETECTION:
  Risk score: {risk_score}/100
  Signals fired: {anomaly_signals}

{{
  "severity": "CRITICAL|HIGH|MEDIUM|LOW",
  "confidence": <integer 0-100>,
  "narrative": "<2-3 sentences: what happened, why suspicious, what it could mean>",
  "recommended_actions": ["<action 1>", "<action 2>", "<action 3>"]
}}"""


def _ip_known(row: pd.Series, baseline: dict | None) -> bool:
    """True if this source_ip is in the user's own historical IPs."""
    if not baseline:
        return False
    return row[config.COL_SOURCE_IP] in baseline.get("seen_ips_own", set())


def build_prompt(row: pd.Series, baseline: dict | None = None) -> str:
    """Render the Gemini prompt for one enriched, scored event."""
    systems = row.get("systems_access_list") or row.get(config.COL_SYSTEMS_ACCESS, "")
    if isinstance(systems, list):
        systems = ", ".join(systems)
    ip_note = "KNOWN" if _ip_known(row, baseline) else "UNKNOWN - not in user history"
    return _PROMPT_TEMPLATE.format(
        username=row.get(config.COL_USERNAME, "?"),
        job_title=row.get(config.COL_JOB_TITLE, "?"),
        department=row.get(config.COL_DEPARTMENT, "?"),
        privilege_level=row.get(config.COL_PRIVILEGE, "?"),
        is_active=row.get(config.COL_IS_ACTIVE, "?"),
        days_inactive=row.get(config.COL_DAYS_INACTIVE, "?"),
        systems_access=systems,
        tenure_months=row.get("tenure_months", "?"),
        timestamp=row.get(config.COL_TIMESTAMP, "?"),
        time_classification=row.get(config.COL_TIME_CLASS, "?"),
        action=row.get(config.COL_ACTION, "?"),
        resource=row.get(config.COL_RESOURCE, "?"),
        resource_sensitivity=row.get(config.COL_SENSITIVITY, "?"),
        status=row.get(config.COL_STATUS, "?"),
        source_ip=row.get(config.COL_SOURCE_IP, "?"),
        ip_note=ip_note,
        risk_score=row.get("adjusted_risk_score", row.get("risk_score", "?")),
        anomaly_signals=row.get("anomaly_signals", ""),
    )


# --- Gemini path (lazy) ----------------------------------------------------
_MODEL_CACHE: list = []  # one-slot cache: [] unset, [None] tried+failed, [model] ready


def _get_model():
    """Lazily configure and cache the Gemini model; return None if unavailable."""
    if _MODEL_CACHE:
        return _MODEL_CACHE[0]
    try:
        from dotenv import load_dotenv
        load_dotenv()
        key = os.getenv("GEMINI_API_KEY")
        if not key or key == "your_api_key_here":
            _MODEL_CACHE.append(None)
            return None
        import google.generativeai as genai
        genai.configure(api_key=key)
        model = genai.GenerativeModel(config.LLM_MODEL)
        _MODEL_CACHE.append(model)
        return model
    except Exception:
        _MODEL_CACHE.append(None)
        return None


def _parse_json(text: str) -> dict:
    """Extract a JSON object from a model response that may be fenced/noisy."""
    cleaned = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
    match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
    return json.loads(match.group(0) if match else cleaned)


def generate_narrative(row: pd.Series, baseline: dict | None = None) -> dict:
    """Call Gemini for one event and return the parsed narrative dict (may raise)."""
    model = _get_model()
    if model is None:
        raise RuntimeError("Gemini model unavailable (no key / package)")
    response = model.generate_content(build_prompt(row, baseline))
    data = _parse_json(response.text)
    data["narrative_source"] = "gemini"
    return data


# --- Deterministic fallback ------------------------------------------------
def _fallback_actions(signals: str, row: pd.Series) -> list[str]:
    """Pick recommended actions from which signals fired."""
    s = signals.lower()
    actions: list[str] = []
    if "export" in s or ("off-hours" in s and row.get(config.COL_SENSITIVITY) == "high"):
        actions.append("Block/quarantine the export and review the data destination for exfiltration")
    if "cross-department" in s or "ungranted" in s:
        actions.append(f"Verify business justification for {row.get(config.COL_DEPARTMENT)} access to {row.get(config.COL_RESOURCE)}")
    if "elevated privilege" in s:
        actions.append("Review the account's privileged-access grants and recent admin activity")
    if "stale account" in s:
        actions.append("Confirm the account is still required; disable if the user has left or is dormant")
    if "failed" in s:
        actions.append("Inspect surrounding events for repeated failures (credential probing)")
    if not actions:
        actions.append("Review the access event with the user's manager for business justification")
    actions.append("Audit this user's access in the surrounding 72 hours")
    return actions[:3]


def _fallback_narrative(row: pd.Series, baseline: dict | None = None) -> dict:
    """Build a deterministic, explainable narrative when Gemini is unavailable."""
    signals = str(row.get("anomaly_signals", ""))
    score = int(row.get("adjusted_risk_score", row.get("risk_score", 0)))
    severity = row.get("adjusted_severity") or row.get("severity", "LOW")
    user = row.get(config.COL_USERNAME, "A user")
    role = f"{row.get(config.COL_JOB_TITLE, '')} in {row.get(config.COL_DEPARTMENT, '')}".strip()
    narrative = (
        f"{user} ({role}, {row.get(config.COL_PRIVILEGE, '')}) performed "
        f"{row.get(config.COL_ACTION)} on {row.get(config.COL_SENSITIVITY)}-sensitivity "
        f"{row.get(config.COL_RESOURCE)} at {row.get(config.COL_TIMESTAMP)} "
        f"({row.get(config.COL_TIME_CLASS)}). "
        f"This scored {score}/100 on: {signals or 'no specific signals'}. "
        f"The combination is consistent with potential insider risk and warrants review."
    )
    return {
        "severity": severity,
        "confidence": min(99, 50 + score // 2),
        "narrative": narrative,
        "recommended_actions": _fallback_actions(signals, row),
        "narrative_source": "fallback",
    }


def generate_narrative_safe(row: pd.Series, baseline: dict | None = None) -> dict:
    """Try Gemini; on any failure return the deterministic fallback narrative."""
    try:
        return generate_narrative(row, baseline)
    except Exception:
        return _fallback_narrative(row, baseline)


def narrate_flagged_incidents(
    scored_df: pd.DataFrame,
    baselines: dict[str, dict] | None = None,
    limit: int | None = None,
    write: bool = True,
) -> pd.DataFrame:
    """Narrate flagged events (risk >= threshold), highest risk first.

    Adds llm_severity / llm_confidence / llm_narrative / llm_recommended_actions /
    narrative_source. ``limit`` caps how many incidents are narrated (to conserve
    Gemini quota); None narrates all flagged. Writes config.FLAGGED_CSV.
    """
    baselines = baselines or {}
    col = "adjusted_risk_score" if "adjusted_risk_score" in scored_df.columns else "risk_score"
    flagged = scored_df[scored_df[col] >= config.RISK_FLAG_THRESHOLD].sort_values(col, ascending=False)
    if limit is not None:
        flagged = flagged.head(limit)

    records = []
    for _, row in flagged.iterrows():
        baseline = baselines.get(row[config.COL_USER_ID])
        n = generate_narrative_safe(row, baseline)
        records.append({
            "llm_severity": n.get("severity"),
            "llm_confidence": n.get("confidence"),
            "llm_narrative": n.get("narrative"),
            "llm_recommended_actions": " | ".join(n.get("recommended_actions", [])),
            "narrative_source": n.get("narrative_source"),
        })
    narratives = pd.DataFrame(records, index=flagged.index)
    out = pd.concat([flagged, narratives], axis=1)

    if write:
        config.DATA_OUTPUT.mkdir(parents=True, exist_ok=True)
        out.to_csv(config.FLAGGED_CSV, index=False)
    return out


if __name__ == "__main__":  # python -m src.llm_narrator
    from src.ingestor import load_access_logs, load_user_profiles, merge_logs_with_profiles
    from src.baseline import build_all_baselines
    from src.detector import score_all_events
    from src.suppressor import apply_suppression

    profiles = load_user_profiles()
    enriched = merge_logs_with_profiles(load_access_logs(), profiles)
    baselines = build_all_baselines(enriched, profiles)
    scored = apply_suppression(score_all_events(enriched, baselines, write=False))
    flagged = narrate_flagged_incidents(scored, baselines)
    src = flagged["narrative_source"].value_counts().to_dict()
    print(f"incidents narrated : {len(flagged)}  source={src}")
    print(f"written to         : {config.FLAGGED_CSV.relative_to(config.ROOT)}\n")
    top = flagged.iloc[0]
    print(f"TOP INCIDENT [{top['adjusted_risk_score']} {top.get('adjusted_severity')}]")
    print(" ", top["llm_narrative"])
    print("  Actions:", top["llm_recommended_actions"])
