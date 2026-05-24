const API_BASE = 'http://127.0.0.1:8000'

async function request(path, options = {}) {
  const res = await fetch(API_BASE + path, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }
  return res.json()
}

export const api = {
  getStats:     ()             => request('/api/stats/'),
  getChartData: (period='24h') => request(`/api/stats/chart-data?period=${period}`),
  getEvents: (params = {}) => {
    const q = new URLSearchParams()
    if (params.limit)      q.set('limit', params.limit)
    if (params.risk_level) q.set('risk_level', params.risk_level)
    if (params.source_ip)  q.set('source_ip', params.source_ip)
    return request(`/api/events/?${q}`)
  },
  getEvent:    (id)   => request(`/api/events/${id}`),
  getBlocked:  ()     => request('/api/blocked'),
  getIPStatus: (ip)   => request(`/api/ip/${ip}`),
  unblockIP:   (ip)   => request(`/api/unblock/${ip}`, { method: 'POST' }),
  blockIP:     (ip)   => request(`/api/block/${ip}`,   { method: 'POST' }),
  createEvent: (data) => request('/api/events/', { method: 'POST', body: JSON.stringify(data) }),
  getSessions: (params = {}) => {
    const q = new URLSearchParams()
    if (params.limit)        q.set('limit', params.limit)
    if (params.session_date) q.set('session_date', params.session_date)
    return request(`/api/sessions/?${q}`)
  },
}