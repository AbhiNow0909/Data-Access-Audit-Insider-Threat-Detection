import { useEffect, useState } from 'react'
import { getHealth, getMetrics, getIncidents, getIncident, getUsers } from './api'
import MetricsPanel from './components/MetricsPanel'
import IncidentDashboard from './components/IncidentDashboard'
import IncidentCard from './components/IncidentCard'
import UserProfile from './components/UserProfile'
import EventTester from './components/EventTester'
import Overview from './components/Overview'
import Icon from './components/ui/Icon'
import { Badge } from './components/ui/Badge'
import { SkeletonStatCards, SkeletonPanel } from './components/ui/Skeleton'

const TABS = [
  { id: 'overview', label: 'Overview', icon: 'grid' },
  { id: 'incidents', label: 'Incidents', icon: 'list' },
  { id: 'users', label: 'Users', icon: 'users' },
  { id: 'test', label: 'Test Event', icon: 'flask' },
]

export default function App() {
  const [health, setHealth] = useState(null)
  const [metrics, setMetrics] = useState(null)
  const [incidents, setIncidents] = useState([])
  const [users, setUsers] = useState([])
  const [view, setView] = useState('overview')
  const [selectedId, setSelectedId] = useState(null)
  const [detail, setDetail] = useState(null)
  const [detailLoading, setDetailLoading] = useState(false)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([getHealth(), getMetrics(), getIncidents(50), getUsers()])
      .then(([h, m, inc, us]) => {
        setHealth(h)
        setMetrics(m)
        setIncidents(inc)
        setUsers(us)
        if (inc.length) setSelectedId(inc[0].incident_id)
      })
      .catch((e) => setError(e.message || 'Failed to reach the API'))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    if (selectedId == null) return
    setDetailLoading(true)
    getIncident(selectedId)
      .then(setDetail)
      .catch(() => setDetail(null))
      .finally(() => setDetailLoading(false))
  }, [selectedId])

  return (
    <div className="min-h-screen">
      <Header health={health} loading={loading} />

      <main className="mx-auto max-w-[1400px] px-4 pb-16 pt-6 sm:px-6">
        {/* Tab navigation */}
        <nav className="mb-5 flex gap-1 overflow-x-auto rounded-2xl border border-white/10 bg-white/[0.03] p-1.5 backdrop-blur-xl">
          {TABS.map((t) => {
            const active = view === t.id
            return (
              <button
                key={t.id}
                onClick={() => setView(t.id)}
                className={`flex shrink-0 items-center gap-2 rounded-xl px-4 py-2 text-sm font-medium transition-all duration-200 ${
                  active
                    ? 'bg-gradient-to-r from-indigo-500 to-violet-500 text-white shadow-lg shadow-indigo-500/25'
                    : 'text-slate-400 hover:bg-white/5 hover:text-slate-200'
                }`}
              >
                <Icon name={t.icon} size={16} />
                {t.label}
              </button>
            )
          })}
        </nav>

        {error ? (
          <ApiError message={error} />
        ) : loading ? (
          <div className="space-y-5">
            <SkeletonStatCards />
            <SkeletonPanel />
          </div>
        ) : (
          <div className="space-y-5">
            <MetricsPanel metrics={metrics} />
            <div key={view} className="animate-fade-up">
              {view === 'overview' ? (
                <Overview />
              ) : view === 'incidents' ? (
                <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.4fr)]">
                  <IncidentDashboard incidents={incidents} selectedId={selectedId} onSelect={setSelectedId} />
                  <IncidentCard incident={detail} loading={detailLoading} />
                </div>
              ) : view === 'users' ? (
                <UserProfile users={users} />
              ) : (
                <EventTester />
              )}
            </div>
          </div>
        )}
      </main>

      <footer className="border-t border-white/5 py-6 text-center text-xs text-slate-600">
        Sentinel · Data Access Audit &amp; Insider Threat Detection · PS-04
        {health?.narrated != null && ` · ${health.narrated} incidents narrated`}
      </footer>
    </div>
  )
}

function Header({ health, loading }) {
  return (
    <header className="sticky top-0 z-30 border-b border-white/5 bg-slate-950/60 backdrop-blur-xl">
      <div className="mx-auto flex max-w-[1400px] items-center justify-between gap-4 px-4 py-3.5 sm:px-6">
        <div className="flex items-center gap-3">
          <span className="grid h-10 w-10 place-items-center rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 text-white shadow-lg shadow-indigo-500/30">
            <Icon name="shield" size={20} />
          </span>
          <div>
            <h1 className="text-base font-bold leading-tight tracking-tight text-white">Sentinel</h1>
            <p className="text-xs text-slate-400">Insider Threat Detection</p>
          </div>
        </div>

        <div className="flex items-center gap-2.5">
          {!loading && health && (
            <>
              <span className="hidden items-center gap-1.5 text-xs text-slate-400 sm:flex">
                <span className="font-semibold text-slate-200">{health.events?.toLocaleString()}</span> events
                <span className="mx-1 text-slate-700">·</span>
                <span className="font-semibold text-slate-200">{health.flagged}</span> flagged
              </span>
              {health.targets_met ? (
                <Badge tone="emerald"><Icon name="check" size={12} /> Targets met</Badge>
              ) : (
                <Badge tone="rose"><Icon name="alert" size={12} /> Below target</Badge>
              )}
            </>
          )}
          <span className="flex items-center gap-1.5 rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[11px] text-slate-400">
            <span className={`h-1.5 w-1.5 rounded-full ${loading ? 'bg-amber-400' : 'bg-emerald-400'} ${loading ? '' : 'animate-pulse'}`} />
            {loading ? 'Connecting' : 'Live'}
          </span>
        </div>
      </div>
    </header>
  )
}

function ApiError({ message }) {
  return (
    <div className="glass animate-scale-in mx-auto mt-10 max-w-md p-8 text-center">
      <span className="mx-auto grid h-12 w-12 place-items-center rounded-xl border border-rose-500/30 bg-rose-500/10 text-rose-400">
        <Icon name="alert" size={22} />
      </span>
      <p className="mt-4 text-lg font-semibold text-white">Cannot reach the API</p>
      <p className="mt-1 text-sm text-slate-400">{message}</p>
      <p className="mt-4 text-xs text-slate-500">
        Start the backend from the project root:
        <code className="mt-1 block rounded-lg bg-slate-900 px-2 py-1.5 text-indigo-300">
          python -m uvicorn api.main:app --reload
        </code>
      </p>
    </div>
  )
}
