"""Central configuration: paths, schema constants, and tunable thresholds.

This is the single source of truth for file locations and column names so no
module hardcodes a path. Schema constants reflect the ACTUAL columns present in
the organizer-provided CSVs (see sample_data/), which differ from early design
docs (no rowcount/destination columns, no separate label files).
"""
from __future__ import annotations

from pathlib import Path

# --- Paths -----------------------------------------------------------------
PROJECT_ROOT: Path = Path(__file__).resolve().parents[1]
DATA_DIR: Path = PROJECT_ROOT / "sample_data"
OUTPUT_DIR: Path = PROJECT_ROOT / "outputs"

ACCESS_LOGS_CSV: Path = DATA_DIR / "data_access_logs.csv"
USER_PROFILES_CSV: Path = DATA_DIR / "user_profiles.csv"

# Ground-truth label files are NOT provided in sample_data. Evaluation falls back
# to a heuristic weak-label scheme (see src/evaluator.py). If real label files are
# added later, point these at them.
ACCESS_LABELS_CSV: Path | None = None
USER_LABELS_CSV: Path | None = None

# --- Access log schema (data_access_logs.csv) ------------------------------
COL_TIMESTAMP = "timestamp"
COL_USER_ID = "user_id"
COL_USERNAME = "username"
COL_ACTION = "action"               # admin_operation|login|sql_query|file_access|export_data|api_call
COL_RESOURCE = "resource"           # HRIS|PROD_DB|Admin_Console|BI_Tool|Customer_Vault|SIEM|Data_Lake|GL_System|Email_Archive|File_Share
COL_SENSITIVITY = "resource_sensitivity"   # low|medium|high
COL_STATUS = "status"               # success|failure
COL_SOURCE_IP = "source_ip"
COL_TIME_CLASS = "time_classification"     # business_hours|night|weekend|unusual_hours

# --- User profile schema (user_profiles.csv) -------------------------------
COL_DEPARTMENT = "department"
COL_JOB_TITLE = "job_title"
COL_PRIVILEGE = "privilege_level"   # user|power-user|admin|service-account
COL_SYSTEMS_ACCESS = "systems_access"      # pipe-separated list, e.g. "Azure_AD|Salesforce"
COL_LAST_LOGIN = "last_login"
COL_DAYS_INACTIVE = "days_inactive"
COL_IS_ACTIVE = "is_active"
COL_HIRE_DATE = "hire_date"

# --- Domain knowledge ------------------------------------------------------
SENSITIVITY_RANK = {"low": 1, "medium": 2, "high": 3, "restricted": 4}
HIGH_RISK_ACTIONS = {"export_data", "admin_operation"}
OFF_HOURS_CLASSES = {"night", "unusual_hours", "weekend"}

# --- Baseline / scoring tunables -------------------------------------------
BASELINE_WINDOW_DAYS = 30           # first N days used as the "normal" training window
RISK_FLAG_THRESHOLD = 50            # risk_score >= this is treated as flagged / sent to LLM
LLM_MODEL = "gemini-2.0-flash"
