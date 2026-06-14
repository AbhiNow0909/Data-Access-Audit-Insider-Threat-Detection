import { useEffect, useState } from 'react'
import {
  PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LabelList,
} from 'recharts'
import { getOverview } from '../api'

const SEV_COLORS = { CRITICAL: '#ef4444', HIGH: '#f97316', MEDIUM: '#f59e0b', LOW: '#64748b' }
const AXIS = '#94a3b8'
const tooltipStyle = { background: '#0f172a', border: '1px solid #334155', borderRadius: 8, color: '#e2e8f0', fontSize: 12 }

function Card({ title, subtitle, children, className = '' }) {
  return (
    <div className={`rounded-xl border border-slate-800 bg-slate-900/40 p-4 ${className}`}>
      <h3 className="text-sm font-medium text-slate-200">{title}</h3>
      {subtitle && <p className="mb-2 text-xs text-slate-500">{subtitle}</p>}
      <div className="mt-2">{children}</div>
    </div>
  )
}

function HBar({ data, color = '#6366f1' }) {
  return (
    <ResponsiveContainer width="100%" height={Math.max(120, data.length * 28)}>
      <BarChart data={data} layout="vertical" margin={{ left: 8, right: 24 }}>
        <XAxis type="number" hide />
        <YAxis type="category" dataKey="name" width={108} tick={{ fill: AXIS, fontSize: 11 }} axisLine={false} tickLine={false} />
        <Tooltip contentStyle={tooltipStyle} cursor={{ fill: '#1e293b55' }} />
        <Bar dataKey="count" fill={color} radius={[0, 4, 4, 0]}>
          <LabelList dataKey="count" position="right" fill={AXIS} fontSize={11} />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

export default function Overview() {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    getOverview().then(setData).catch((e) => setError(e.message || 'Failed to load overview'))
  }, [])

  if (error) return <p className="text-sm text-red-400">{error}</p>
  if (!data) return <p className="text-sm text-slate-500">Loading charts…</p>

  const flaggedPct = ((100 * data.flagged) / data.total).toFixed(1)

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      {/* Severity donut */}
      <Card title="Severity distribution" subtitle={`${data.total} events · ${data.flagged} flagged (${flaggedPct}%)`}>
        <ResponsiveContainer width="100%" height={240}>
          <PieChart>
            <Pie data={data.severity} dataKey="count" nameKey="name" innerRadius={55} outerRadius={90} paddingAngle={2}>
              {data.severity.map((s) => <Cell key={s.name} fill={SEV_COLORS[s.name]} stroke="#0f172a" />)}
            </Pie>
            <Tooltip contentStyle={tooltipStyle} />
          </PieChart>
        </ResponsiveContainer>
        <div className="mt-1 flex flex-wrap justify-center gap-3">
          {data.severity.map((s) => (
            <span key={s.name} className="flex items-center gap-1.5 text-xs text-slate-300">
              <span className="inline-block h-2.5 w-2.5 rounded-sm" style={{ background: SEV_COLORS[s.name] }} />
              {s.name} <span className="text-slate-500">{s.count}</span>
            </span>
          ))}
        </div>
      </Card>

      {/* Risk histogram */}
      <Card title="Risk score distribution" subtitle={`flag threshold = ${data.threshold} (bars at/above are flagged)`}>
        <ResponsiveContainer width="100%" height={240}>
          <BarChart data={data.risk_histogram} margin={{ left: -16, right: 8 }}>
            <XAxis dataKey="bin" tick={{ fill: AXIS, fontSize: 10 }} axisLine={{ stroke: '#334155' }} tickLine={false} />
            <YAxis tick={{ fill: AXIS, fontSize: 11 }} axisLine={false} tickLine={false} />
            <Tooltip contentStyle={tooltipStyle} cursor={{ fill: '#1e293b55' }} />
            <Bar dataKey="count" radius={[4, 4, 0, 0]}>
              {data.risk_histogram.map((d) => {
                const lo = parseInt(d.bin.split('-')[0], 10)
                return <Cell key={d.bin} fill={lo >= data.threshold ? '#6366f1' : '#475569'} />
              })}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </Card>

      {/* Breakdowns */}
      <Card title="Flagged incidents by department">
        <HBar data={data.by_department} color="#6366f1" />
      </Card>
      <Card title="Flagged incidents by resource">
        <HBar data={data.by_resource} color="#0ea5e9" />
      </Card>
      <Card title="Flagged incidents by time of day" className="lg:col-span-2">
        <HBar data={data.by_time} color="#a855f7" />
      </Card>
    </div>
  )
}
