import { sevStyle } from '../../util'

// Severity pill with a status dot.
export function SeverityBadge({ severity, className = '' }) {
  const s = sevStyle(severity)
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-[11px] font-semibold ${s.badge} ${className}`}>
      <span className={`h-1.5 w-1.5 rounded-full ${s.dot}`} />
      {severity}
    </span>
  )
}

// Generic tone badge (emerald / rose / slate / indigo).
const TONES = {
  emerald: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300',
  rose: 'border-rose-500/30 bg-rose-500/10 text-rose-300',
  indigo: 'border-indigo-500/30 bg-indigo-500/10 text-indigo-300',
  slate: 'border-white/10 bg-white/5 text-slate-300',
}

export function Badge({ tone = 'slate', children, className = '' }) {
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-[11px] font-medium ${TONES[tone]} ${className}`}>
      {children}
    </span>
  )
}
