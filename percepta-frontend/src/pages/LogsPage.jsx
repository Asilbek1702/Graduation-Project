import { useState, useEffect } from 'react'
import { api } from '../api'

const LOGS_PER_PAGE = 10

export default function LogsPage() {
  const [events, setEvents] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)

  useEffect(() => {
    api.getEvents({ limit: 200 }).then(data => {
      setEvents(data)
    }).catch(e => {
      console.error('Logs API error:', e)
    }).finally(() => setLoading(false))
  }, [])

  // Logs page shows events as session-style activity log
  const filtered = events.filter(e => {
    if (!search) return true
    return e.source_ip.includes(search) || e.event_id.toLowerCase().includes(search.toLowerCase())
  })

  const totalPages = Math.max(1, Math.ceil(filtered.length / LOGS_PER_PAGE))
  const pageLogs = filtered.slice((page-1)*LOGS_PER_PAGE, page*LOGS_PER_PAGE)
  const activeCount = events.filter(e => e.action_taken === 'RATE_LIMIT' || e.action_taken === 'MONITOR').length

  function formatTime(iso) {
    try { return new Date(iso).toTimeString().slice(0,8) } catch { return '—' }
  }

  const ACTION_STATUS = {
    TEMP_BLOCK: { label:'BLOCKED',  cls:'b-critical' },
    RATE_LIMIT: { label:'ACTIVE',   cls:'b-high' },
    MONITOR:    { label:'WATCHING', cls:'b-monitor' },
    LOG:        { label:'LOGGED',   cls:'b-log' },
  }

  return (
    <div style={{ padding: 20 }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ width: 36, height: 36, borderRadius: 8, background: 'rgba(99,179,237,0.1)', color: '#63b3ed', border: '1px solid rgba(99,179,237,0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
          </div>
          <div>
            <div style={{ fontSize: 18, fontWeight: 700 }}>Activity Logs</div>
            <div style={{ fontSize: 11, color: 'var(--text2)' }}>User session tracking and network activity</div>
          </div>
        </div>
        <button style={{ padding: '7px 14px', borderRadius: 7, fontSize: 11, fontWeight: 600, background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border2)', color: 'var(--text2)', cursor: 'pointer', fontFamily: 'var(--font)', display: 'flex', alignItems: 'center', gap: 6 }}>
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
          Export Today
        </button>
      </div>

      {/* Stats */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14, marginBottom: 18 }}>
        <div style={{ background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 10, padding: '14px 16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6 }}>
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#22d3ee" strokeWidth="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/></svg>
          </div>
          <div style={{ fontSize: 10, color: 'var(--text2)', marginBottom: 4 }}>Total Events</div>
          <div style={{ fontSize: 22, fontWeight: 700 }}>{loading ? '...' : events.length}</div>
        </div>
        <div style={{ background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 10, padding: '14px 16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6 }}>
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#10b981" strokeWidth="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
          </div>
          <div style={{ fontSize: 10, color: 'var(--text2)', marginBottom: 4 }}>Active Flows</div>
          <div style={{ fontSize: 22, fontWeight: 700, color: 'var(--green)' }}>{loading ? '...' : activeCount}</div>
        </div>
      </div>

      {/* Search */}
      <div style={{ position: 'relative', marginBottom: 16 }}>
        <span style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text3)', display: 'flex', pointerEvents: 'none' }}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
        </span>
        <input value={search} onChange={e => { setSearch(e.target.value); setPage(1) }} placeholder="Search by IP address or event ID..."
          style={{ width: '100%', background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 8, padding: '9px 14px 9px 36px', color: 'var(--text)', fontSize: 12, fontFamily: 'var(--font)', outline: 'none' }}
          onFocus={e => e.target.style.borderColor='rgba(34,211,238,0.3)'}
          onBlur={e => e.target.style.borderColor='var(--border)'}
        />
      </div>

      {/* Table */}
      <div style={{ background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 10, overflow: 'hidden', marginBottom: 14 }}>
        <div style={{ padding: '14px 18px', borderBottom: '1px solid var(--border)', fontSize: 13, fontWeight: 600, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <span>Event Activity Log</span>
          <span style={{ fontSize: 10, color: 'var(--text3)', fontWeight: 400 }}>real-time network events</span>
        </div>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr>
              {['Event ID','Source IP','Destination','Time','Risk','Action','Status'].map(h => (
                <th key={h} style={{ padding: '10px 16px', textAlign: 'left', fontSize: 9, fontWeight: 600, letterSpacing: 1, textTransform: 'uppercase', color: 'var(--text3)', background: 'rgba(255,255,255,0.02)', borderBottom: '1px solid var(--border)' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading
              ? <tr><td colSpan={7} style={{ textAlign: 'center', padding: 30, color: 'var(--text3)', fontSize: 12 }}>Loading...</td></tr>
              : pageLogs.length === 0
                ? <tr><td colSpan={7} style={{ textAlign: 'center', padding: 30, color: 'var(--text3)', fontSize: 12 }}>No events found</td></tr>
                : pageLogs.map(e => {
                  const st = ACTION_STATUS[e.action_taken] || { label: e.action_taken, cls: 'b-log' }
                  return (
                    <tr key={e.event_id} style={{ borderBottom: '1px solid rgba(255,255,255,0.03)', transition: 'background 0.1s' }}
                      onMouseOver={r => r.currentTarget.style.background='rgba(255,255,255,0.03)'}
                      onMouseOut={r => r.currentTarget.style.background='transparent'}>
                      <td style={{ padding: '11px 16px' }}><span className="evtid-mono">{e.event_id}</span></td>
                      <td style={{ padding: '11px 16px' }}><span className="ip-mono">{e.source_ip}</span></td>
                      <td style={{ padding: '11px 16px' }}><span className="ip-mono">{e.destination_ip}:{e.destination_port}</span></td>
                      <td style={{ padding: '11px 16px' }}><span className="time-mono">{formatTime(e.timestamp)}</span></td>
                      <td style={{ padding: '11px 16px' }}><span className={`badge ${{ LOW:'b-low', MEDIUM:'b-medium', HIGH:'b-high', CRITICAL:'b-critical' }[e.risk_level]||'b-log'}`}>{e.risk_level}</span></td>
                      <td style={{ padding: '11px 16px', color: 'var(--text2)', fontSize: 11, fontFamily: 'monospace' }}>{e.action_taken}</td>
                      <td style={{ padding: '11px 16px' }}><span className={`badge ${st.cls}`}>{st.label}</span></td>
                    </tr>
                  )
                })
            }
          </tbody>
        </table>

        {/* Pagination */}
        {totalPages > 1 && (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '14px 18px', borderTop: '1px solid var(--border)', gap: 4 }}>
            <button onClick={() => setPage(p => Math.max(1,p-1))} disabled={page===1}
              style={{ width: 30, height: 30, borderRadius: 6, border: '1px solid var(--border)', background: 'transparent', color: 'var(--text2)', cursor: page===1?'not-allowed':'pointer', opacity: page===1?0.3:1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="15 18 9 12 15 6"/></svg>
            </button>
            {Array.from({ length: totalPages }, (_,i) => i+1).map(p => (
              <button key={p} onClick={() => setPage(p)} style={{ width: 30, height: 30, borderRadius: 6, border: `1px solid ${p===page?'rgba(34,211,238,0.3)':'var(--border)'}`, background: p===page?'var(--cyan-dim)':'transparent', color: p===page?'var(--cyan)':'var(--text2)', cursor: 'pointer', fontFamily: 'var(--font)', fontSize: 11, fontWeight: 600, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>{p}</button>
            ))}
            <button onClick={() => setPage(p => Math.min(totalPages,p+1))} disabled={page===totalPages}
              style={{ width: 30, height: 30, borderRadius: 6, border: '1px solid var(--border)', background: 'transparent', color: 'var(--text2)', cursor: page===totalPages?'not-allowed':'pointer', opacity: page===totalPages?0.3:1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="9 18 15 12 9 6"/></svg>
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
