"""Central configuration: paths, schema constants, and tunable thresholds.

Single source of truth for file locations so no module hardcodes a path.
`data/raw/` is read-only (organizer files); the pipeline only ever writes to
`data/output/`. Schema constants reflect the ACTUAL organizer columns.
"""
from __future__ import annotations

from pathlib import Path

# --- Paths -----------------------------------------------------------------
ROOT: Path = Path(__file__).resolve().parent
DATA_RAW: Path = ROOT / "data" / "raw"
DATA_OUTPUT: Path = ROOT / "data" / "output"

LOGS_CSV: Path = DATA_RAW / "data_access_logs.csv"
PROFILES_CSV: Path = DATA_RAW / "user_profiles.csv"

SCORED_CSV: Path = DATA_OUTPUT / "scored_incidents.csv"      # all events + scores
FLAGGED_CSV: Path = DATA_OUTPUT / "flagged_incidents.csv"    # risk>=50 + narratives
LABELS_CSV: Path = DATA_OUTPUT / "derived_labels.csv"        # rule-derived ground truth

# Tier-3: drop organizer label files here and point this at them when available.
ORGANIZER_LABELS_CSV: Path | None = None

# --- Access log schema (data/raw/data_access_logs.csv) ---------------------
COL_TIMESTAMP = "timestamp"
COL_USER_ID = "user_id"
COL_USERNAME = "username"
COL_ACTION = "action"               # login|sql_query|api_call|file_access|export_data|admin_operation
COL_RESOURCE = "resource"           # HRIS|PROD_DB|Admin_Console|BI_Tool|Customer_Vault|SIEM|Data_Lake|GL_System|Email_Archive|File_Share
COL_SENSITIVITY = "resource_sensitivity"   # low|medium|high
COL_STATUS = "status"               # success|failure
COL_SOURCE_IP = "source_ip"
COL_TIME_CLASS = "time_classification"     # business_hours|unusual_hours|night|weekend

# --- User profile schema (data/raw/user_profiles.csv) ----------------------
COL_DEPARTMENT = "department"
COL_JOB_TITLE = "job_title"
COL_PRIVILEGE = "privilege_level"   # user|power-user|admin|service-account
COL_SYSTEMS_ACCESS = "systems_access"      # pipe-separated, parsed to list in ingestor
COL_LAST_LOGIN = "last_login"
COL_DAYS_INACTIVE = "days_inactive"
COL_IS_ACTIVE = "is_active"
COL_HIRE_DATE = "hire_date"

# --- Domain knowledge ------------------------------------------------------
SENSITIVITY_RANK = {"low": 1, "medium": 2, "high": 3, "restricted": 4}
OFF_HOURS_CLASSES = {"night", "unusual_hours", "weekend"}
FINANCE_DEPARTMENTS = {"Finance", "Accounting"}

# Dim 3 (inappropriate resource access): which department(s) legitimately "own"
# each sensitive resource. Access by anyone outside the owner set is cross-domain
# and scored by sensitivity. Resources NOT listed (BI_Tool, File_Share, PROD_DB)
# are treated as broadly accessible. Tunable — adjust to the org's reality.
RESOURCE_OWNER_DEPARTMENTS: dict[str, set[str]] = {
    "HRIS": {"HR"},
    "GL_System": {"Finance"},
    "Customer_Vault": {"Sales", "Support", "Marketing"},
    "Admin_Console": {"IT", "Security"},
    "SIEM": {"Security", "IT"},
    "Data_Lake": {"Engineering", "IT"},
    "Email_Archive": {"Legal", "Compliance"},
}
# The only resources whose names actually appear in the systems_access grant
# vocabulary, so a "not in grant" check is meaningful for these alone.
GRANT_CHECKABLE_RESOURCES: set[str] = {"PROD_DB", "SIEM"}

# --- Pipeline tunables -----------------------------------------------------
# The data is sparse (~12 events/user/year), so a fixed 30-day training window
# leaves most users with no baseline. Baselines are built from each user's FULL
# history, with a cohort fallback (by privilege_level) for thin/zero users.
BASELINE_MIN_EVENTS = 5             # below this a user's baseline is low_confidence
# Operating threshold: selected on the derived labels to satisfy P>0.75 AND
# R>0.70 (the detector weights themselves are not fitted to the labels).
RISK_FLAG_THRESHOLD = 40            # risk_score >= this is flagged / sent to LLM
LLM_MODEL = "gemini-2.0-flash"

# Severity bands from composite risk_score (0-100), aligned to the flag threshold
# (flagged == MEDIUM or above) and the observed score range (max ~78).
SEVERITY_BANDS = [(60, "CRITICAL"), (50, "HIGH"), (40, "MEDIUM"), (0, "LOW")]
