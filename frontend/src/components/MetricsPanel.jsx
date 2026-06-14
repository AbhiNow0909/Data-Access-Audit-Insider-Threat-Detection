import StatCard from './ui/StatCard'
import { Badge } from './ui/Badge'
import Icon from './ui/Icon'

const pct = (v) => `${(v * 100).toFixed(1)}%`

function TargetPill({ ok, target }) {
  return ok ? (
    <Badge tone="emerald"><Icon name="check" size={11} /> &gt;{target}</Badge>
  ) : (
    <Badge tone="rose"><Icon name="alert" size={11} /> &lt;{target}</Badge>
  )
}

// KPI row: animated Precision / Recall / F1 + volume + critical recall.
export default function MetricsPanel({ metrics }) {
  if (!metrics) return null
  const t2 = metrics.tier2_derived
  const t1 = metrics.tier1_critical

  return (
    <section className="grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-5">
      <StatCard
        icon="target" tone="emerald" label="Precision" value={t2.precision}
        format={pct} pill={<TargetPill ok={t2.precision >= 0.75} target="75%" />} delay={0}
      />
      <StatCard
        icon="activity" tone="sky" label="Recall" value={t2.recall}
        format={pct} pill={<TargetPill ok={t2.recall >= 0.7} target="70%" />} delay={60}
      />
      <StatCard
        icon="trendingUp" tone="indigo" label="F1 Score" value={t2.f1}
        format={pct} pill={<TargetPill ok={t2.f1 >= 0.72} target="72%" />} delay={120}
      />
      <StatCard
        icon="list" tone="amber" label="Flagged" value={t2.flagged}
        format={(v) => Math.round(v)} sub={`of ${t2.n} · TP ${t2.tp} · FP ${t2.fp}`} delay={180}
      />
      <StatCard
        icon="shield" tone="rose" label="Critical recall" value={t1.recall}
        format={pct} sub={`${t1.caught}/${t1.critical_anomalies} caught`} delay={240}
      />
    </section>
  )
}
