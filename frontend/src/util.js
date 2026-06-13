// Severity -> Tailwind classes for badges and accents.
export const SEVERITY_STYLES = {
  CRITICAL: { badge: 'bg-red-500/20 text-red-300 border-red-500/40', bar: 'bg-red-500', dot: 'bg-red-500' },
  HIGH: { badge: 'bg-orange-500/20 text-orange-300 border-orange-500/40', bar: 'bg-orange-500', dot: 'bg-orange-500' },
  MEDIUM: { badge: 'bg-amber-500/20 text-amber-300 border-amber-500/40', bar: 'bg-amber-500', dot: 'bg-amber-500' },
  LOW: { badge: 'bg-slate-500/20 text-slate-300 border-slate-500/40', bar: 'bg-slate-500', dot: 'bg-slate-500' },
}

export const sevStyle = (sev) => SEVERITY_STYLES[sev] || SEVERITY_STYLES.LOW

export const riskColor = (score) =>
  score >= 60 ? 'text-red-400' : score >= 50 ? 'text-orange-400' : score >= 40 ? 'text-amber-400' : 'text-slate-400'

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
