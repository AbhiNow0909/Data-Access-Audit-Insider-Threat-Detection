import { useCountUp } from '../../hooks/useCountUp'
import Icon from './Icon'

const TONES = {
  indigo: 'border-indigo-500/20 bg-indigo-500/10 text-indigo-300',
  emerald: 'border-emerald-500/20 bg-emerald-500/10 text-emerald-300',
  rose: 'border-rose-500/20 bg-rose-500/10 text-rose-300',
  amber: 'border-amber-400/20 bg-amber-400/10 text-amber-300',
  sky: 'border-sky-500/20 bg-sky-500/10 text-sky-300',
}

// Premium KPI card with an animated counter, icon and optional target/trend pill.
export default function StatCard({ icon, label, value, format = (v) => Math.round(v), tone = 'indigo', sub, pill, delay = 0 }) {
  const n = useCountUp(value)
  return (
    <div className="glass glass-hover animate-fade-up p-4" style={{ animationDelay: `${delay}ms` }}>
      <div className="flex items-center justify-between">
        <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">{label}</span>
        {icon && (
          <span className={`grid h-8 w-8 place-items-center rounded-lg border ${TONES[tone]}`}>
            <Icon name={icon} size={16} />
          </span>
        )}
      </div>
      <div className="mt-3 text-3xl font-bold tracking-tight text-white tabular-nums">{format(n)}</div>
      <div className="mt-1 flex items-center gap-2">
        {pill}
        {sub && <span className="text-xs text-slate-500">{sub}</span>}
      </div>
    </div>
  )
}
