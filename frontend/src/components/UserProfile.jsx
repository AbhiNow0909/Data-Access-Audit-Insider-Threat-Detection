import { riskColor } from '../util'

// Per-user behavioral overview: privilege, dormancy, max risk, flagged-event count.
export default function UserProfile({ users }) {
  return (
    <div className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900/40">
      <div className="border-b border-slate-800 px-4 py-3 text-sm font-medium text-slate-300">
        User risk profiles ({users.length})
      </div>
      <div className="max-h-[72vh] overflow-y-auto">
        <table className="w-full text-sm">
          <thead className="sticky top-0 bg-slate-900 text-left text-xs uppercase tracking-wide text-slate-400">
            <tr>
              <th className="px-4 py-2 font-medium">User</th>
              <th className="px-4 py-2 font-medium">Dept</th>
              <th className="px-4 py-2 font-medium">Privilege</th>
              <th className="px-4 py-2 font-medium">Inactive</th>
              <th className="px-4 py-2 font-medium">Flagged</th>
              <th className="px-4 py-2 font-medium">Max risk</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {users.map((u) => (
              <tr key={u.user_id} className="hover:bg-slate-800/40">
                <td className="px-4 py-2">
                  <div className="font-medium text-slate-200">{u.username}</div>
                  <div className="text-xs text-slate-500">{u.job_title}</div>
                </td>
                <td className="px-4 py-2 text-slate-400">{u.department}</td>
                <td className="px-4 py-2">
                  <span className="rounded bg-slate-800 px-1.5 py-0.5 text-xs text-slate-300">{u.privilege_level}</span>
                </td>
                <td className="px-4 py-2 text-slate-400 tabular-nums">{u.days_inactive}d</td>
                <td className="px-4 py-2 tabular-nums text-slate-300">{u.flagged_events}</td>
                <td className={`px-4 py-2 text-right font-semibold tabular-nums ${riskColor(u.max_risk_score)}`}>
                  {u.max_risk_score}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
