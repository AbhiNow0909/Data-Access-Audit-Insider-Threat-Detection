import { sevStyle, riskColor, fmtTime } from '../util'

// Prioritized, clickable list of flagged incidents.
export default function IncidentDashboard({ incidents, selectedId, onSelect }) {
  return (
    <div className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900/40">
      <div className="border-b border-slate-800 px-4 py-3 text-sm font-medium text-slate-300">
        Prioritized incidents ({incidents.length})
      </div>
      <ul className="max-h-[70vh] divide-y divide-slate-800 overflow-y-auto">
        {incidents.map((inc) => {
          const s = sevStyle(inc.adjusted_severity)
          const active = inc.incident_id === selectedId
          return (
            <li key={inc.incident_id}>
              <button
                onClick={() => onSelect(inc.incident_id)}
                className={`flex w-full items-center gap-3 px-4 py-3 text-left transition hover:bg-slate-800/50 ${
                  active ? 'bg-slate-800/70' : ''
                }`}
              >
                <span className={`text-lg font-bold tabular-nums ${riskColor(inc.adjusted_risk_score)}`}>
                  {inc.adjusted_risk_score}
                </span>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className={`rounded border px-1.5 py-0.5 text-[10px] font-semibold ${s.badge}`}>
                      {inc.adjusted_severity}
                    </span>
                    <span className="truncate text-sm font-medium text-slate-200">{inc.username}</span>
                    <span className="text-xs text-slate-500">{inc.department}</span>
                  </div>
                  <div className="mt-0.5 truncate text-xs text-slate-400">
                    {inc.action} · {inc.resource} · {inc.resource_sensitivity} · {inc.time_classification}
                  </div>
                </div>
                <span className="shrink-0 text-[10px] text-slate-500">{fmtTime(inc.timestamp)}</span>
              </button>
            </li>
          )
        })}
      </ul>
    </div>
  )
}
