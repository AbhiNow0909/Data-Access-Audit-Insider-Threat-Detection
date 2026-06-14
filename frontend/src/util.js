// Severity -> Tailwind classes + chart hex, used across the app.
export const SEVERITY_STYLES = {
  CRITICAL: { badge: 'border-rose-500/30 bg-rose-500/10 text-rose-300', dot: 'bg-rose-500', bar: 'bg-rose-500', hex: '#f43f5e', glow: 'shadow-rose-500/20' },
  HIGH: { badge: 'border-orange-500/30 bg-orange-500/10 text-orange-300', dot: 'bg-orange-500', bar: 'bg-orange-500', hex: '#f97316', glow: 'shadow-orange-500/20' },
  MEDIUM: { badge: 'border-amber-400/30 bg-amber-400/10 text-amber-300', dot: 'bg-amber-400', bar: 'bg-amber-400', hex: '#fbbf24', glow: 'shadow-amber-400/20' },
  LOW: { badge: 'border-slate-500/30 bg-slate-500/10 text-slate-300', dot: 'bg-slate-500', bar: 'bg-slate-500', hex: '#64748b', glow: 'shadow-slate-500/10' },
}

export const sevStyle = (sev) => SEVERITY_STYLES[sev] || SEVERITY_STYLES.LOW

export const riskColor = (score) =>
  score >= 60 ? 'text-rose-400' : score >= 50 ? 'text-orange-400' : score >= 40 ? 'text-amber-300' : 'text-slate-400'

export const riskBar = (score) =>
  score >= 60 ? 'bg-rose-500' : score >= 50 ? 'bg-orange-500' : score >= 40 ? 'bg-amber-400' : 'bg-slate-600'

export const fmtPct = (x) => (x == null ? 'n/a' : `${(x * 100).toFixed(1)}%`)

export const fmtTime = (iso) => {
  if (!iso) return ''
  try {
    return new Date(iso).toLocaleString(undefined, {
      month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit',
    })
  } catch {
    return iso
  }
}
