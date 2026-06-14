import { sevStyle, riskColor, fmtTime } from '../util'
import { SeverityBadge } from './ui/Badge'
import Icon from './ui/Icon'
import { Skeleton } from './ui/Skeleton'

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
      <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-white/5">
        <div
          className={`h-full rounded-full transition-[width] duration-700 ease-out ${value ? 'bg-gradient-to-r from-indigo-500 to-violet-500' : 'bg-slate-700'}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  )
}

function Panel({ children }) {
  return <div className="glass p-5">{children}</div>
}

export default function IncidentCard({ incident, loading }) {
  if (loading) {
    return (
      <Panel>
        <Skeleton className="h-6 w-24" />
        <Skeleton className="mt-3 h-5 w-2/3" />
        <Skeleton className="mt-2 h-4 w-1/2" />
        <div className="mt-5 space-y-3">{Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-4 w-full" />)}</div>
      </Panel>
    )
  }
  if (!incident) {
    return (
      <Panel>
        <div className="flex h-64 flex-col items-center justify-center text-center text-slate-500">
          <Icon name="list" size={28} className="text-slate-600" />
          <p className="mt-2 text-sm">Select an incident to view its analysis.</p>
        </div>
      </Panel>
    )
  }

  const s = sevStyle(incident.adjusted_severity)
  const signals = (incident.anomaly_signals || '').split('; ').filter(Boolean)
  const actions = (incident.llm_recommended_actions || '').split(' | ').filter(Boolean)

  return (
    <Panel>
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <SeverityBadge severity={incident.adjusted_severity} />
            <span className="text-xs text-slate-500">#{incident.incident_id}</span>
          </div>
          <h2 className="mt-2 text-lg font-semibold text-slate-100">
            {incident.username}
            <span className="text-sm font-normal text-slate-400"> · {incident.job_title}, {incident.department} · {incident.privilege_level}</span>
          </h2>
          <p className="mt-1 text-sm text-slate-400">
            {incident.action} on <span className="text-slate-200">{incident.resource}</span> ({incident.resource_sensitivity}) ·{' '}
            {incident.status} · {fmtTime(incident.timestamp)} ({incident.time_classification}) · IP {incident.source_ip}
          </p>
        </div>
        <div className={`shrink-0 rounded-2xl border px-4 py-2 text-center ${s.badge}`}>
          <div className={`text-4xl font-bold tabular-nums ${riskColor(incident.adjusted_risk_score)}`}>
            {incident.adjusted_risk_score}
          </div>
          <div className="text-[10px] uppercase tracking-wide text-slate-500">risk / 100</div>
        </div>
      </div>

      <div className="mt-5 grid gap-2.5">
        {DIMS.map((d) => <DimBar key={d.key} label={d.label} value={incident[d.key]} max={d.max} />)}
      </div>

      {signals.length > 0 && (
        <div className="mt-5">
          <h3 className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">Anomaly signals</h3>
          <ul className="mt-1.5 flex flex-wrap gap-1.5">
            {signals.map((sig, i) => <li key={i} className="chip">{sig}</li>)}
          </ul>
        </div>
      )}

      <div className="mt-5 rounded-xl border border-indigo-500/20 bg-gradient-to-br from-indigo-500/10 to-violet-500/5 p-4">
        <div className="flex items-center justify-between">
          <h3 className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wider text-indigo-200">
            <Icon name="sparkles" size={13} /> Analyst narrative
          </h3>
          <span className="text-[10px] text-slate-400">
            {incident.narrative_source === 'gemini' ? 'Gemini 2.0 Flash' : 'rule-based fallback'}
            {incident.llm_confidence != null && ` · ${incident.llm_confidence}% confidence`}
          </span>
        </div>
        <p className="mt-1.5 text-sm leading-relaxed text-slate-200">{incident.llm_narrative}</p>
      </div>

      {actions.length > 0 && (
        <div className="mt-5">
          <h3 className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">Recommended actions</h3>
          <ol className="mt-1.5 space-y-1.5">
            {actions.map((a, i) => (
              <li key={i} className="flex gap-2.5 text-sm text-slate-300">
                <span className="mt-0.5 grid h-5 w-5 shrink-0 place-items-center rounded-full bg-indigo-500/15 text-[11px] font-semibold text-indigo-300">{i + 1}</span>
                {a}
              </li>
            ))}
          </ol>
        </div>
      )}

      {incident.suppressed && (
        <p className="mt-4 flex items-center gap-1.5 rounded-lg border border-amber-400/20 bg-amber-400/5 px-3 py-2 text-xs text-amber-300/90">
          <Icon name="alert" size={13} /> Suppression applied: {incident.suppression_reason}
        </p>
      )}
    </Panel>
  )
}
