import { useMemo, useState } from 'react'
import { riskColor, riskBar } from '../util'
import Icon from './ui/Icon'

const COLUMNS = [
  { key: 'username', label: 'User', sortable: false },
  { key: 'department', label: 'Dept', sortable: false },
  { key: 'privilege_level', label: 'Privilege', sortable: false },
  { key: 'days_inactive', label: 'Inactive', sortable: true, align: 'right' },
  { key: 'flagged_events', label: 'Flagged', sortable: true, align: 'right' },
  { key: 'max_risk_score', label: 'Max risk', sortable: true, align: 'right' },
]

// Per-user behavioral overview — searchable + sortable.
export default function UserProfile({ users }) {
  const [query, setQuery] = useState('')
  const [sort, setSort] = useState({ key: 'max_risk_score', dir: 'desc' })

  const rows = useMemo(() => {
    const q = query.trim().toLowerCase()
    let out = users.filter((u) =>
      !q || [u.username, u.department, u.job_title, u.privilege_level].some((f) => String(f).toLowerCase().includes(q)))
    out = [...out].sort((a, b) => {
      const av = a[sort.key], bv = b[sort.key]
      return sort.dir === 'desc' ? bv - av : av - bv
    })
    return out
  }, [users, query, sort])

  const toggleSort = (key) =>
    setSort((s) => (s.key === key ? { key, dir: s.dir === 'desc' ? 'asc' : 'desc' } : { key, dir: 'desc' }))

  return (
    <div className="glass overflow-hidden">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-white/5 p-3">
        <h3 className="flex items-center gap-2 text-sm font-semibold text-slate-200">
          <Icon name="users" size={15} className="text-indigo-300" /> User risk profiles
          <span className="rounded-full bg-white/5 px-1.5 py-0.5 text-[11px] text-slate-400">{rows.length}</span>
        </h3>
        <div className="relative w-full sm:w-64">
          <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-500"><Icon name="search" size={15} /></span>
          <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search users…" className="input pl-9" />
        </div>
      </div>

      <div className="max-h-[68vh] overflow-auto">
        <table className="w-full text-sm">
          <thead className="sticky top-0 z-10 bg-slate-900/90 backdrop-blur">
            <tr className="text-left text-[11px] uppercase tracking-wider text-slate-400">
              {COLUMNS.map((c) => (
                <th
                  key={c.key}
                  onClick={c.sortable ? () => toggleSort(c.key) : undefined}
                  className={`px-4 py-2.5 font-semibold ${c.align === 'right' ? 'text-right' : ''} ${c.sortable ? 'cursor-pointer select-none hover:text-slate-200' : ''}`}
                >
                  <span className={`inline-flex items-center gap-1 ${c.align === 'right' ? 'flex-row-reverse' : ''}`}>
                    {c.label}
                    {c.sortable && (
                      <Icon name="sort" size={12} className={sort.key === c.key ? 'text-indigo-300' : 'text-slate-600'} />
                    )}
                  </span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {rows.map((u) => (
              <tr key={u.user_id} className="transition hover:bg-white/[0.04]">
                <td className="px-4 py-2.5">
                  <div className="font-medium text-slate-200">{u.username}</div>
                  <div className="text-xs text-slate-500">{u.job_title}</div>
                </td>
                <td className="px-4 py-2.5 text-slate-400">{u.department}</td>
                <td className="px-4 py-2.5"><span className="chip">{u.privilege_level}</span></td>
                <td className="px-4 py-2.5 text-right tabular-nums text-slate-400">{u.days_inactive}d</td>
                <td className="px-4 py-2.5 text-right tabular-nums text-slate-300">{u.flagged_events}</td>
                <td className="px-4 py-2.5">
                  <div className="flex items-center justify-end gap-2">
                    <div className="hidden h-1.5 w-16 overflow-hidden rounded-full bg-white/5 sm:block">
                      <div className={`h-full rounded-full ${riskBar(u.max_risk_score)}`} style={{ width: `${Math.min(100, u.max_risk_score)}%` }} />
                    </div>
                    <span className={`w-7 text-right font-semibold tabular-nums ${riskColor(u.max_risk_score)}`}>{u.max_risk_score}</span>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
