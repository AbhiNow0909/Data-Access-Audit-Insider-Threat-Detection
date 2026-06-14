import { useMemo, useState } from 'react'
import { sevStyle, riskColor, fmtTime } from '../util'
import { SeverityBadge } from './ui/Badge'
import Icon from './ui/Icon'

const FILTERS = ['ALL', 'CRITICAL', 'HIGH', 'MEDIUM']

// Prioritized, searchable, clickable list of flagged incidents.
export default function IncidentDashboard({ incidents, selectedId, onSelect }) {
  const [query, setQuery] = useState('')
  const [sev, setSev] = useState('ALL')

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    return incidents.filter((inc) => {
      if (sev !== 'ALL' && inc.adjusted_severity !== sev) return false
      if (!q) return true
      return [inc.username, inc.department, inc.resource, inc.action]
        .some((f) => String(f).toLowerCase().includes(q))
    })
  }, [incidents, query, sev])

  return (
    <div className="glass overflow-hidden">
      <div className="border-b border-white/5 p-3">
        <div className="flex items-center justify-between gap-2">
          <h3 className="flex items-center gap-2 text-sm font-semibold text-slate-200">
            <Icon name="list" size={15} className="text-indigo-300" /> Incidents
            <span className="rounded-full bg-white/5 px-1.5 py-0.5 text-[11px] text-slate-400">{filtered.length}</span>
          </h3>
        </div>
        <div className="relative mt-2.5">
          <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-500">
            <Icon name="search" size={15} />
          </span>
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search user, resource, department…"
            className="input pl-9"
          />
        </div>
        <div className="mt-2.5 flex gap-1.5">
          {FILTERS.map((f) => (
            <button
              key={f}
              onClick={() => setSev(f)}
              className={`rounded-lg px-2.5 py-1 text-[11px] font-medium transition ${
                sev === f ? 'bg-indigo-500/20 text-indigo-200 ring-1 ring-indigo-500/40' : 'text-slate-400 hover:bg-white/5'
              }`}
            >
              {f === 'ALL' ? 'All' : f}
            </button>
          ))}
        </div>
      </div>

      <ul className="max-h-[64vh] divide-y divide-white/5 overflow-y-auto">
        {filtered.length === 0 && (
          <li className="p-6 text-center text-sm text-slate-500">No incidents match.</li>
        )}
        {filtered.map((inc) => {
          const s = sevStyle(inc.adjusted_severity)
          const active = inc.incident_id === selectedId
          return (
            <li key={inc.incident_id}>
              <button
                onClick={() => onSelect(inc.incident_id)}
                className={`group flex w-full items-center gap-3 px-4 py-3 text-left transition-all ${
                  active ? 'bg-indigo-500/10' : 'hover:bg-white/[0.04]'
                }`}
              >
                <span className={`h-9 w-1 shrink-0 rounded-full ${active ? s.bar : 'bg-transparent group-hover:bg-white/10'}`} />
                <span className={`w-9 text-center text-lg font-bold tabular-nums ${riskColor(inc.adjusted_risk_score)}`}>
                  {inc.adjusted_risk_score}
                </span>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <SeverityBadge severity={inc.adjusted_severity} />
                    <span className="truncate text-sm font-medium text-slate-200">{inc.username}</span>
                    <span className="text-xs text-slate-500">{inc.department}</span>
                  </div>
                  <div className="mt-0.5 truncate text-xs text-slate-400">
                    {inc.action} · {inc.resource} · {inc.resource_sensitivity} · {inc.time_classification}
                  </div>
                </div>
                <span className="hidden shrink-0 text-[10px] text-slate-500 sm:block">{fmtTime(inc.timestamp)}</span>
                <Icon name="arrowRight" size={14} className={`shrink-0 transition ${active ? 'text-indigo-300' : 'text-slate-600 group-hover:text-slate-400'}`} />
              </button>
            </li>
          )
        })}
      </ul>
    </div>
  )
}
