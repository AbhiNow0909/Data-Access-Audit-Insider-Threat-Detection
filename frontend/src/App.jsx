import { useEffect, useState } from 'react'
import { getHealth, getMetrics, getIncidents, getIncident, getUsers } from './api'
import MetricsPanel from './components/MetricsPanel'
import IncidentDashboard from './components/IncidentDashboard'
import IncidentCard from './components/IncidentCard'
import UserProfile from './components/UserProfile'

export default function App() {
  const [health, setHealth] = useState(null)
  const [metrics, setMetrics] = useState(null)
  const [incidents, setIncidents] = useState([])
  const [users, setUsers] = useState([])
  const [view, setView] = useState('incidents')
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

  if (loading) return <Center>Loading pipeline results…</Center>
  if (error) {
    return (
      <Center>
        <div className="max-w-md text-center">
          <p className="text-lg font-semibold text-red-400">Cannot reach the API</p>
          <p className="mt-2 text-sm text-slate-400">{error}</p>
          <p className="mt-3 text-xs text-slate-500">
            Start the backend from the project root:{' '}
            <code className="rounded bg-slate-800 px-1.5 py-0.5">uvicorn api.main:app --reload</code>
          </p>
        </div>
      </Center>
    )
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-6">
      <header className="mb-5 flex items-end justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-100">Data Access Audit &amp; Insider Threat Detection</h1>
          <p className="text-sm text-slate-400">
            {health?.events} events analyzed · {health?.flagged} flagged ·{' '}
            <span className={health?.targets_met ? 'text-emerald-400' : 'text-red-400'}>
              targets {health?.targets_met ? 'met' : 'not met'}
            </span>
          </p>
        </div>
        <div className="flex gap-1 rounded-lg border border-slate-800 bg-slate-900 p-1">
          {['incidents', 'users'].map((v) => (
            <button
              key={v}
              onClick={() => setView(v)}
              className={`rounded px-3 py-1 text-sm capitalize transition ${
                view === v ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              {v}
            </button>
          ))}
        </div>
      </header>

      <MetricsPanel metrics={metrics} />

      <main className="mt-5">
        {view === 'incidents' ? (
          <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.4fr)]">
            <IncidentDashboard incidents={incidents} selectedId={selectedId} onSelect={setSelectedId} />
            <IncidentCard incident={detail} loading={detailLoading} />
          </div>
        ) : (
          <UserProfile users={users} />
        )}
      </main>

      <footer className="mt-8 text-center text-xs text-slate-600">
        Narratives: {health?.narrated} incidents · Insider Threat Detection · PS-04
      </footer>
    </div>
  )
}

function Center({ children }) {
  return <div className="flex min-h-screen items-center justify-center px-4 text-slate-300">{children}</div>
}
