# Architecture

5-layer pipeline: **Ingest → Baseline → Score → Suppress → Narrate**, plus
Evaluate. See `CLAUDE.md` for the full design. This doc is filled in as each
layer lands.

## Data reality (as shipped in `sample_data/`)

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
  (hour/time-class distribution, typical resources, action mix per user).
- **Scoring dimensions adapt to available signals**: time deviation,
  sensitivity, first-time-resource access, high-risk action, failed access,
  and access outside the user's `systems_access` grant. Volume-spike and
  destination-risk (the original dims 2 & 4) have no source columns.
- **Evaluation** uses a transparent heuristic weak-label scheme until real
  labels are supplied (see `docs/` + `src/evaluator.py`).
