import { useState } from 'react'
import { scoreEvent } from '../api'
import { sevStyle, riskColor } from '../util'
import { SeverityBadge } from './ui/Badge'
import Icon from './ui/Icon'

const ACTIONS = ['login', 'sql_query', 'api_call', 'file_access', 'export_data', 'admin_operation']
const RESOURCES = ['HRIS', 'PROD_DB', 'Admin_Console', 'BI_Tool', 'Customer_Vault', 'SIEM',
  'Data_Lake', 'GL_System', 'Email_Archive', 'File_Share']
const SENSITIVITY = ['low', 'medium', 'high']
const STATUS = ['success', 'failure']
const TIME_CLASS = ['business_hours', 'unusual_hours', 'weekend', 'night']
const PRIVILEGE = ['user', 'power-user', 'admin', 'service-account']
const DEPARTMENTS = ['Marketing', 'Finance', 'Support', 'Engineering', 'Sales', 'HR',
  'Security', 'Compliance', 'Operations', 'IT', 'Legal', 'Executive']

const DEFAULTS = {
  username: 'bob.jones', department: 'IT', job_title: 'Analyst', privilege_level: 'user',
  action: 'export_data', resource: 'Customer_Vault', resource_sensitivity: 'high',
  status: 'success', time_classification: 'night', source_ip: '203.0.113.7',
  systems_access: '', days_inactive: 2, is_active: true, tenure_months: 3,
  timestamp: '2026-04-15 03:47:12',
}

const DIMS = [
  { key: 'time', label: 'Time', max: 20 },
  { key: 'action_sensitivity', label: 'Action × Sensitivity', max: 25 },
  { key: 'resource', label: 'Inappropriate resource', max: 25 },
  { key: 'stale', label: 'Stale account', max: 15 },
  { key: 'privilege', label: 'Privilege × off-hours', max: 15 },
]

const inputCls = 'input'

function Field({ label, children }) {
  return (
    <label className="block">
      <span className="mb-1 block text-[11px] font-medium uppercase tracking-wide text-slate-400">{label}</span>
      {children}
    </label>
  )
}

function Select({ name, value, onChange, options }) {
  return (
    <select name={name} value={value} onChange={onChange} className={inputCls}>
      {options.map((o) => <option key={o} value={o} className="bg-slate-900">{o}</option>)}
    </select>
  )
}

function DimBar({ label, value, max }) {
  const pct = Math.round((100 * (value || 0)) / max)
  return (
    <div>
      <div className="flex justify-between text-xs text-slate-400"><span>{label}</span><span className="tabular-nums">{value || 0}/{max}</span></div>
      <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-white/5">
        <div className={`h-full rounded-full transition-[width] duration-700 ease-out ${value ? 'bg-gradient-to-r from-indigo-500 to-violet-500' : 'bg-slate-700'}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}

export default function EventTester() {
  const [form, setForm] = useState(DEFAULTS)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const update = (e) => {
    const { name, value, type, checked } = e.target
    setForm((f) => ({ ...f, [name]: type === 'checkbox' ? checked : value }))
  }

  const submit = async (e) => {
    e.preventDefault()
    setLoading(true); setError(null)
    try {
      const payload = { ...form, days_inactive: Number(form.days_inactive), tenure_months: Number(form.tenure_months) }
      setResult(await scoreEvent(payload))
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Scoring failed')
      setResult(null)
    } finally {
      setLoading(false)
    }
  }

  const s = result ? sevStyle(result.severity) : null

  return (
    <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
      {/* Form */}
      <form onSubmit={submit} className="glass p-5">
        <h2 className="flex items-center gap-2 text-sm font-semibold text-slate-200">
          <Icon name="flask" size={15} className="text-indigo-300" /> Test an access event
        </h2>
        <p className="mt-1 text-xs text-slate-500">
          Score any event + actor through the live pipeline — an unseen user is fine (scored against cohort norms).
        </p>

        <p className="mt-4 text-[11px] font-semibold uppercase tracking-wider text-indigo-300/80">Actor</p>
        <div className="mt-2 grid grid-cols-2 gap-3">
          <Field label="Username"><input name="username" value={form.username} onChange={update} className={inputCls} /></Field>
          <Field label="Department"><Select name="department" value={form.department} onChange={update} options={DEPARTMENTS} /></Field>
          <Field label="Job title"><input name="job_title" value={form.job_title} onChange={update} className={inputCls} /></Field>
          <Field label="Privilege"><Select name="privilege_level" value={form.privilege_level} onChange={update} options={PRIVILEGE} /></Field>
          <Field label="Days inactive"><input name="days_inactive" type="number" value={form.days_inactive} onChange={update} className={inputCls} /></Field>
          <Field label="Tenure (months)"><input name="tenure_months" type="number" value={form.tenure_months} onChange={update} className={inputCls} /></Field>
          <Field label="Systems access (a|b)"><input name="systems_access" value={form.systems_access} onChange={update} className={inputCls} placeholder="PROD_DB|SIEM" /></Field>
          <label className="flex items-end gap-2 pb-2 text-sm text-slate-300">
            <input name="is_active" type="checkbox" checked={form.is_active} onChange={update} className="h-4 w-4 accent-indigo-500" />
            Account is active
          </label>
        </div>

        <p className="mt-4 text-[11px] font-semibold uppercase tracking-wider text-indigo-300/80">Event</p>
        <div className="mt-2 grid grid-cols-2 gap-3">
          <Field label="Action"><Select name="action" value={form.action} onChange={update} options={ACTIONS} /></Field>
          <Field label="Resource"><Select name="resource" value={form.resource} onChange={update} options={RESOURCES} /></Field>
          <Field label="Sensitivity"><Select name="resource_sensitivity" value={form.resource_sensitivity} onChange={update} options={SENSITIVITY} /></Field>
          <Field label="Status"><Select name="status" value={form.status} onChange={update} options={STATUS} /></Field>
          <Field label="Time class"><Select name="time_classification" value={form.time_classification} onChange={update} options={TIME_CLASS} /></Field>
          <Field label="Source IP"><input name="source_ip" value={form.source_ip} onChange={update} className={inputCls} /></Field>
          <div className="col-span-2"><Field label="Timestamp"><input name="timestamp" value={form.timestamp} onChange={update} className={inputCls} /></Field></div>
        </div>

        <button type="submit" disabled={loading} className="btn-primary mt-5 w-full">
          {loading ? (
            <><span className="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white" /> Scoring…</>
          ) : (
            <><Icon name="zap" size={15} /> Score event</>
          )}
        </button>
        {error && <p className="mt-2 flex items-center gap-1.5 text-xs text-rose-400"><Icon name="alert" size={13} /> {error}</p>}
      </form>

      {/* Result */}
      <div className="glass p-5">
        {!result ? (
          <div className="flex h-full min-h-[20rem] flex-col items-center justify-center text-center text-slate-500">
            <Icon name="sparkles" size={28} className="text-slate-600" />
            <p className="mt-2 text-sm">Submit an event to see its risk analysis.</p>
          </div>
        ) : (
          <div className="animate-scale-in">
            <div className="flex items-start justify-between">
              <SeverityBadge severity={result.severity} />
              <div className={`rounded-2xl border px-4 py-2 text-center ${s.badge}`}>
                <div className={`text-4xl font-bold tabular-nums ${riskColor(result.risk_score)}`}>{result.risk_score}</div>
                <div className="text-[10px] uppercase tracking-wide text-slate-500">risk / 100</div>
              </div>
            </div>

            <div className="mt-5 grid gap-2.5">
              {DIMS.map((d) => <DimBar key={d.key} label={d.label} value={result.dimension_scores[d.key]} max={d.max} />)}
            </div>

            {result.anomaly_signals.length > 0 && (
              <div className="mt-5">
                <h3 className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">Anomaly signals</h3>
                <ul className="mt-1.5 flex flex-wrap gap-1.5">
                  {result.anomaly_signals.map((sig, i) => <li key={i} className="chip">{sig}</li>)}
                </ul>
              </div>
            )}

            <div className="mt-5 rounded-xl border border-indigo-500/20 bg-gradient-to-br from-indigo-500/10 to-violet-500/5 p-4">
              <div className="flex items-center justify-between">
                <h3 className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wider text-indigo-200">
                  <Icon name="sparkles" size={13} /> Analyst narrative
                </h3>
                <span className="text-[10px] text-slate-400">
                  {result.narrative_source === 'gemini' ? 'Gemini 2.0 Flash' : 'rule-based fallback'}
                  {result.confidence != null && ` · ${result.confidence}% confidence`}
                </span>
              </div>
              <p className="mt-1.5 text-sm leading-relaxed text-slate-200">{result.narrative}</p>
            </div>

            {result.recommended_actions.length > 0 && (
              <div className="mt-5">
                <h3 className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">Recommended actions</h3>
                <ol className="mt-1.5 space-y-1.5">
                  {result.recommended_actions.map((a, i) => (
                    <li key={i} className="flex gap-2.5 text-sm text-slate-300">
                      <span className="mt-0.5 grid h-5 w-5 shrink-0 place-items-center rounded-full bg-indigo-500/15 text-[11px] font-semibold text-indigo-300">{i + 1}</span>
                      {a}
                    </li>
                  ))}
                </ol>
              </div>
            )}

            {result.suppression && (
              <p className="mt-4 flex items-center gap-1.5 rounded-lg border border-amber-400/20 bg-amber-400/5 px-3 py-2 text-xs text-amber-300/90">
                <Icon name="alert" size={13} /> Suppression applied: {result.suppression}
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
