import { sevStyle, riskColor, fmtTime } from '../util'

const DIMS = [
  { key: 'dim1_time', label: 'Time', max: 20 },
  { key: 'dim2_action_sensitivity', label: 'Action × Sensitivity', max: 25 },
  { key: 'dim3_resource', label: 'Inappropriate resource', max: 25 },
  { key: 'dim4_stale', label: 'Stale account', max: 15 },
  { key: 'dim5_privilege', label: 'Privilege × off-hours', max: 15 },
]

function DimBar({ label, value, max }) {
  const pct = Math.round((100 * (value || 0)) / max)
  return (
    <div>
      <div className="flex justify-between text-xs text-slate-400">
        <span>{label}</span>
        <span className="tabular-nums">{value || 0}/{max}</span>
      </div>
      <div className="mt-1 h-1.5 rounded bg-slate-800">
        <div className={`h-1.5 rounded ${value ? 'bg-indigo-500' : 'bg-slate-700'}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}

// Drill-down detail for one incident: scores, signals, narrative, actions.
export default function IncidentCard({ incident, loading }) {
  if (loading) return <Panel><p className="text-slate-400">Loading incident…</p></Panel>
  if (!incident) return <Panel><p className="text-slate-500">Select an incident to view details.</p></Panel>

  const s = sevStyle(incident.adjusted_severity)
  const signals = (incident.anomaly_signals || '').split('; ').filter(Boolean)
  const actions = (incident.llm_recommended_actions || '').split(' | ').filter(Boolean)

  return (
    <Panel>
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span className={`rounded border px-2 py-0.5 text-xs font-semibold ${s.badge}`}>
              {incident.adjusted_severity}
            </span>
            <span className="text-sm text-slate-400">#{incident.incident_id}</span>
          </div>
          <h2 className="mt-2 text-lg font-semibold text-slate-100">
            {incident.username} <span className="text-sm font-normal text-slate-400">
              · {incident.job_title}, {incident.department} · {incident.privilege_level}</span>
          </h2>
          <p className="mt-1 text-sm text-slate-400">
            {incident.action} on <span className="text-slate-200">{incident.resource}</span> ({incident.resource_sensitivity}) ·{' '}
            {incident.status} · {fmtTime(incident.timestamp)} ({incident.time_classification}) · IP {incident.source_ip}
          </p>
        </div>
        <div className="text-right">
          <div className={`text-4xl font-bold tabular-nums ${riskColor(incident.adjusted_risk_score)}`}>
            {incident.adjusted_risk_score}
          </div>
          <div className="text-xs text-slate-500">risk / 100</div>
        </div>
      </div>

      <div className="mt-4 grid gap-2">
        {DIMS.map((d) => <DimBar key={d.key} label={d.label} value={incident[d.key]} max={d.max} />)}
      </div>

      {signals.length > 0 && (
        <div className="mt-4">
          <h3 className="text-xs uppercase tracking-wide text-slate-400">Anomaly signals</h3>
          <ul className="mt-1 flex flex-wrap gap-1.5">
            {signals.map((sig, i) => (
              <li key={i} className="rounded bg-slate-800 px-2 py-1 text-xs text-slate-300">{sig}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="mt-4 rounded-lg border border-slate-800 bg-slate-950/50 p-3">
        <div className="flex items-center justify-between">
          <h3 className="text-xs uppercase tracking-wide text-slate-400">Analyst narrative</h3>
          <span className="text-[10px] text-slate-500">
            {incident.narrative_source === 'gemini' ? 'Gemini 2.0 Flash' : 'rule-based fallback'}
            {incident.llm_confidence != null && ` · ${incident.llm_confidence}% confidence`}
          </span>
        </div>
        <p className="mt-1 text-sm leading-relaxed text-slate-200">{incident.llm_narrative}</p>
      </div>

      {actions.length > 0 && (
        <div className="mt-4">
          <h3 className="text-xs uppercase tracking-wide text-slate-400">Recommended actions</h3>
          <ol className="mt-1 list-decimal space-y-1 pl-5 text-sm text-slate-300">
            {actions.map((a, i) => <li key={i}>{a}</li>)}
          </ol>
        </div>
      )}

      {incident.suppressed && (
        <p className="mt-3 text-xs text-amber-400/80">⚠ Suppression applied: {incident.suppression_reason}</p>
      )}
    </Panel>
  )
}

function Panel({ children }) {
  return <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-5">{children}</div>
}
