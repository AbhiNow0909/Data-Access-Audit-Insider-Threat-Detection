# Architecture

5-layer pipeline: **Ingest → Baseline → Score → Suppress → Narrate**, plus
Evaluate. See `CLAUDE.md` for the full design. This doc is filled in as each
layer lands.

## Data reality (as shipped in `data/raw/`)

The actual organizer CSVs differ from the early design assumptions:

| Designed for | Actually available |
|---|---|
| `data_access_labels.csv`, `user_profile_labels.csv` | **Not provided** — no ground-truth labels |
| `rowcount`, `destination`, `data_asset` columns | Not present |
| profile `typical_access_hours`, `avg_*`, `high_risk_flag`, `tenure_months` | Not present |

**Access logs** (`data_access_logs.csv`, 1,200 rows, Apr 2025–Apr 2026):
`timestamp, user_id, username, action, resource, resource_sensitivity, status,
source_ip, time_classification`

**User profiles** (`user_profiles.csv`, 100 rows):
`user_id, username, email, department, job_title, privilege_level,
systems_access, last_login, days_inactive, is_active, hire_date`

### Consequences for the design
- **Baselines are learned from the logs**, not read from profile columns
  (seen IPs, time-class distribution, typical resources, action mix per user).
- **5-dimension scoring over real columns** (see CLAUDE.md for point matrices):
  (1) time, (2) action x sensitivity, (3) unauthorized system access vs
  `systems_access`, (4) stale/inactive account, (5) IP & privilege. The
  original volume-spike and destination-risk dims are dropped — no source columns.
- **Three-tier evaluation** (`src/evaluator.py`): Tier 1 known-anomaly recall,
  Tier 2 full P/R/F1 vs rule-derived labels (`src/labeler.py`), Tier 3 plug-in
  organizer labels when available.
