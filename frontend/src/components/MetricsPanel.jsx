import { fmtPct } from '../util'

// Precision / Recall / F1 cards with target comparison, plus volume + per-severity recall.
export default function MetricsPanel({ metrics }) {
  if (!metrics) return null
  const t2 = metrics.tier2_derived
  const t1 = metrics.tier1_critical
  const cards = [
    { label: 'Precision', val: t2.precision, target: 0.75 },
    { label: 'Recall', val: t2.recall, target: 0.7 },
    { label: 'F1 Score', val: t2.f1, target: 0.72 },
  ]

  return (
    <section className="grid grid-cols-2 gap-3 md:grid-cols-5">
      {cards.map((c) => {
        const ok = c.val >= c.target
        return (
          <div key={c.label} className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
            <div className="text-xs uppercase tracking-wide text-slate-400">{c.label}</div>
            <div className={`mt-1 text-2xl font-semibold ${ok ? 'text-emerald-400' : 'text-red-400'}`}>
              {fmtPct(c.val)}
            </div>
            <div className="mt-1 text-xs text-slate-500">
              target &gt;{(c.target * 100).toFixed(0)}% {ok ? '✓' : '✗'}
            </div>
          </div>
        )
      })}

      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
        <div className="text-xs uppercase tracking-wide text-slate-400">Flagged</div>
        <div className="mt-1 text-2xl font-semibold text-slate-100">
          {t2.flagged}
          <span className="text-sm text-slate-500"> / {t2.n}</span>
        </div>
        <div className="mt-1 text-xs text-slate-500">
          TP {t2.tp} · FP {t2.fp} · FN {t2.fn}
        </div>
      </div>

      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
        <div className="text-xs uppercase tracking-wide text-slate-400">Critical recall</div>
        <div className="mt-1 text-2xl font-semibold text-slate-100">{fmtPct(t1.recall)}</div>
        <div className="mt-1 text-xs text-slate-500">
          {t1.caught} / {t1.critical_anomalies} caught
        </div>
      </div>
    </section>
  )
}
