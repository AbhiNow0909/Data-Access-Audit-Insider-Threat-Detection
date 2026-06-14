import axios from 'axios'

// Backend base URL; override with VITE_API_URL if the API runs elsewhere.
const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const api = axios.create({ baseURL, timeout: 120000 })

export const getHealth = () => api.get('/health').then((r) => r.data)
export const getMetrics = () => api.get('/metrics').then((r) => r.data)
export const getIncidents = (limit = 50) =>
  api.get('/incidents', { params: { limit } }).then((r) => r.data)
export const getIncident = (id) => api.get(`/incidents/${id}`).then((r) => r.data)
export const getUsers = () => api.get('/users').then((r) => r.data)
export const getOverview = () => api.get('/overview').then((r) => r.data)
export const scoreEvent = (payload) => api.post('/score', payload).then((r) => r.data)

export default api
