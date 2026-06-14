import { useEffect, useState } from 'react'
import {
  PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LabelList,
} from 'recharts'
import { getOverview } from '../api'
import Card, { CardHeader } from './ui/Card'
import Icon from './ui/Icon'
import { Skeleton } from './ui/Skeleton'

const SEV_COLORS = { CRITICAL: '#f43f5e', HIGH: '#f97316', MEDIUM: '#fbbf24', LOW: '#64748b' }
const AXIS = '#94a3b8'
const tooltipStyle = {
  background: 'rgba(15,23,42,0.95)', border: '1px solid rgba(99,102,241,0.3)',
  borderRadius: 12, color: '#e2e8f0', fontSize: 12, boxShadow: '0 8px 30px rgba(2,6,23,0.6)',
}

function HBar({ data, from, to }) {
  const id = `g-${from.replace('#', '')}`
  return (
    <ResponsiveContainer width="100%" height={Math.max(130, data.length * 30)}>
      <BarChart data={data} layout="vertical" margin={{ left: 8, right: 28 }}>
        <defs>
          <linearGradient id={id} x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor={from} />
            <stop offset="100%" stopColor={to} />
          </linearGradient>
        </defs>
        <XAxis type="number" hide />
        <YAxis type="category" dataKey="name" width={112} tick={{ fill: AXIS, fontSize: 11 }} axisLine={false} tickLine={false} />
        <Tooltip contentStyle={tooltipStyle} cursor={{ fill: 'rgba(99,102,241,0.08)' }} />
        <Bar dataKey="count" fill={`url(#${id})`} radius={[0, 6, 6, 0]} barSize={16}>
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

  if (error) return <p className="text-sm text-rose-400">{error}</p>
  if (!data) {
    return (
      <div className="grid gap-4 lg:grid-cols-2">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="glass p-5"><Skeleton className="h-4 w-40" /><Skeleton className="mt-4 h-56 w-full" /></div>
        ))}
      </div>
    )
  }

  const flaggedPct = ((100 * data.flagged) / data.total).toFixed(1)

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      {/* Severity donut */}
      <Card className="p-5" hover delay={0}>
        <CardHeader title="Severity distribution" subtitle={`${data.total.toLocaleString()} events analyzed`} icon={<Icon name="shield" size={16} />} />
        <div className="relative mt-2">
          <ResponsiveContainer width="100%" height={232}>
            <PieChart>
              <Pie data={data.severity} dataKey="count" nameKey="name" innerRadius={62} outerRadius={92} paddingAngle={2} stroke="none">
                {data.severity.map((s) => <Cell key={s.name} fill={SEV_COLORS[s.name]} />)}
              </Pie>
              <Tooltip contentStyle={tooltipStyle} />
            </PieChart>
          </ResponsiveContainer>
          <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-3xl font-bold tabular-nums text-white">{data.flagged}</span>
            <span className="text-xs text-slate-500">flagged ({flaggedPct}%)</span>
          </div>
        </div>
        <div className="mt-2 flex flex-wrap justify-center gap-3">
          {data.severity.map((s) => (
            <span key={s.name} className="flex items-center gap-1.5 text-xs text-slate-300">
              <span className="inline-block h-2.5 w-2.5 rounded-sm" style={{ background: SEV_COLORS[s.name] }} />
              {s.name} <span className="text-slate-500">{s.count}</span>
            </span>
          ))}
        </div>
      </Card>

      {/* Risk histogram */}
      <Card className="p-5" hover delay={80}>
        <CardHeader title="Risk score distribution" subtitle={`flag threshold = ${data.threshold}`} icon={<Icon name="activity" size={16} />} />
        <ResponsiveContainer width="100%" height={264}>
          <BarChart data={data.risk_histogram} margin={{ left: -16, right: 8, top: 12 }}>
            <defs>
              <linearGradient id="flagged" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#818cf8" /><stop offset="100%" stopColor="#6366f1" />
              </linearGradient>
            </defs>
            <XAxis dataKey="bin" tick={{ fill: AXIS, fontSize: 10 }} axisLine={{ stroke: '#1e293b' }} tickLine={false} />
            <YAxis tick={{ fill: AXIS, fontSize: 11 }} axisLine={false} tickLine={false} />
            <Tooltip contentStyle={tooltipStyle} cursor={{ fill: 'rgba(99,102,241,0.08)' }} />
            <Bar dataKey="count" radius={[6, 6, 0, 0]}>
              {data.risk_histogram.map((d) => {
                const lo = parseInt(d.bin.split('-')[0], 10)
                return <Cell key={d.bin} fill={lo >= data.threshold ? 'url(#flagged)' : '#334155'} />
              })}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
        <p className="mt-1 text-center text-xs text-slate-500">
          <span className="inline-block h-2 w-2 rounded-sm bg-indigo-500 align-middle" /> flagged ≥ {data.threshold}
          <span className="mx-2 text-slate-700">·</span>
          <span className="inline-block h-2 w-2 rounded-sm bg-slate-600 align-middle" /> below threshold
        </p>
      </Card>

      {/* Breakdowns */}
      <Card className="p-5" hover delay={160}>
        <CardHeader title="Flagged by department" icon={<Icon name="users" size={16} />} />
        <div className="mt-2"><HBar data={data.by_department} from="#6366f1" to="#a855f7" /></div>
      </Card>
      <Card className="p-5" hover delay={240}>
        <CardHeader title="Flagged by resource" icon={<Icon name="database" size={16} />} />
        <div className="mt-2"><HBar data={data.by_resource} from="#0ea5e9" to="#6366f1" /></div>
      </Card>
      <Card className="p-5 lg:col-span-2" hover delay={320}>
        <CardHeader title="Flagged by time of day" icon={<Icon name="clock" size={16} />} />
        <div className="mt-2"><HBar data={data.by_time} from="#a855f7" to="#ec4899" /></div>
      </Card>
    </div>
  )
}
