import { useState, useEffect } from 'react'
import { api } from '../api'

const LOGS_PER_PAGE = 10

function normalizeSearch(value) {
  return String(value ?? '')
    .normalize('NFKC')
    .replace(/[\u200B-\u200D\uFEFF]/g, '')
    .trim()
    .toLowerCase()
}

function matchesSearch(values, query) {
  const q = normalizeSearch(query)
  if (!q) return true
  return values.some(value => normalizeSearch(value).includes(q))
}

function formatBytes(b) {
  if (!b && b !== 0) return '—'
  if (b >= 1_073_741_824) return (b / 1_073_741_824).toFixed(2) + ' GB'
  if (b >= 1_048_576)     return (b / 1_048_576).toFixed(1) + ' MB'
  if (b >= 1024)          return (b / 1024).toFixed(1) + ' KB'
  return b + ' B'
}

function formatDuration(loginIso, logoutIso) {
  if (!loginIso || !logoutIso) return '—'
  const diff = Math.max(0, Math.floor((new Date(logoutIso) - new Date(loginIso)) / 1000))
  const h = Math.floor(diff / 3600)
  const m = Math.floor((diff % 3600) / 60)
  const s = diff % 60
  if (h > 0) return `${h}h ${m}m`
  if (m > 0) return `${m}m ${s}s`
  return `${s}s`
}

function formatTime(iso) {
  if (!iso) return '—'
  try { return new Date(iso).toTimeString().slice(0, 8) } catch { return '—' }
}

export default function LogsPage() {
  const [sessions, setSessions] = useState([])
  const [loading, setLoading]   = useState(true)
  const [search, setSearch]     = useState('')

  const [page, setPage]         = useState(1)
  const [exporting, setExporting] = useState(false)

  useEffect(() => {
    api.getSessions({ limit: 500 })
      .then(data => setSessions(data))
      .catch(e => console.error('Sessions API error:', e))
      .finally(() => setLoading(false))
  }, [])

  // Filter
  const filtered = sessions.filter(s => {
    return matchesSearch([
      s.ip_address,
      s.session_id,
      s.event_id,
      s.session_date,
      formatTime(s.login_time),
    ], search)
  })

  // Sort by login_time (desc = largest/newest first)
  const sorted = [...filtered].sort((a, b) => {
    const ta = new Date(a.login_time).getTime()
    const tb = new Date(b.login_time).getTime()
    return tb - ta
  })

  const totalPages = Math.max(1, Math.ceil(sorted.length / LOGS_PER_PAGE))
  const pageRows   = sorted.slice((page - 1) * LOGS_PER_PAGE, page * LOGS_PER_PAGE)
  const activeCount = sessions.filter(s => s.status === 'ACTIVE').length

  async function handleExport() {
    setExporting(true)
    try {
      const res = await fetch('http://127.0.0.1:8000/api/sessions/export')
      if (!res.ok) throw new Error('Export failed')
      const blob = await res.blob()
      const url  = URL.createObjectURL(blob)
      const a    = document.createElement('a')
      a.href     = url
      const today = new Date().toISOString().slice(0, 10)
      a.download = `sessions_${today}.xlsx`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch (e) {
      console.error('Export error:', e)
      alert('Export failed. Make sure openpyxl is installed:\npip install openpyxl')
    } finally {
      setExporting(false)
    }
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
        <button onClick={handleExport} disabled={exporting}
          style={{ padding: '7px 14px', borderRadius: 7, fontSize: 11, fontWeight: 600, background: exporting ? 'rgba(34,211,238,0.05)' : 'rgba(255,255,255,0.05)', border: '1px solid var(--border2)', color: exporting ? 'var(--cyan)' : 'var(--text2)', cursor: exporting ? 'wait' : 'pointer', fontFamily: 'var(--font)', display: 'flex', alignItems: 'center', gap: 6 }}>
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
          {exporting ? 'Exporting...' : 'Export Today'}
        </button>
      </div>

      {/* Stats */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14, marginBottom: 18 }}>
        <div style={{ background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 10, padding: '14px 16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6 }}>
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#22d3ee" strokeWidth="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/></svg>
          </div>
          <div style={{ fontSize: 10, color: 'var(--text2)', marginBottom: 4 }}>Total Sessions</div>
          <div style={{ fontSize: 22, fontWeight: 700 }}>{loading ? '...' : sessions.length}</div>
        </div>
        <div style={{ background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 10, padding: '14px 16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6 }}>
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#10b981" strokeWidth="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
          </div>
          <div style={{ fontSize: 10, color: 'var(--text2)', marginBottom: 4 }}>Active Users</div>
          <div style={{ fontSize: 22, fontWeight: 700, color: 'var(--green)' }}>{loading ? '...' : activeCount}</div>
        </div>
      </div>

      {/* Search */}
      <div style={{ position: 'relative', marginBottom: 16 }}>
        <span style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text3)', display: 'flex', pointerEvents: 'none' }}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
        </span>
        <input value={search} onChange={e => { setSearch(e.target.value); setPage(1) }}
          placeholder="Search by IP address, user or date..."
          style={{ width: '100%', background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 8, padding: '9px 14px 9px 36px', color: 'var(--text)', fontSize: 12, fontFamily: 'var(--font)', outline: 'none', boxSizing: 'border-box' }}
          onFocus={e => e.target.style.borderColor = 'rgba(34,211,238,0.3)'}
          onBlur={e => e.target.style.borderColor = 'var(--border)'}
        />
      </div>

      {/* Session Log table */}
      <div style={{ background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 10, overflow: 'hidden', marginBottom: 14 }}>
        <div style={{ padding: '14px 18px', borderBottom: '1px solid var(--border)', fontSize: 13, fontWeight: 600, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <span>Session Log</span>
          <span style={{ fontSize: 10, color: 'var(--text3)', fontWeight: 400 }}>showing user network sessions</span>
        </div>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr>
              {['Event ID', 'IP Address', 'Login Time', 'Logout Time', 'Duration', 'Traffic Used', 'Status'].map(h => (
                <th key={h} style={{ padding: '10px 16px', textAlign: 'left', fontSize: 9, fontWeight: 600, letterSpacing: 1, textTransform: 'uppercase', color: 'var(--text3)', background: 'rgba(255,255,255,0.02)', borderBottom: '1px solid var(--border)' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading
              ? <tr><td colSpan={7} style={{ textAlign: 'center', padding: 30, color: 'var(--text3)', fontSize: 12 }}>Loading...</td></tr>
              : pageRows.length === 0
                ? <tr><td colSpan={7} style={{ textAlign: 'center', padding: 30, color: 'var(--text3)', fontSize: 12 }}>No sessions found</td></tr>
                : pageRows.map(s => (
                  <tr key={s.session_id}
                    style={{ borderBottom: '1px solid rgba(255,255,255,0.03)', transition: 'background 0.1s' }}
                    onMouseOver={r => r.currentTarget.style.background = 'rgba(255,255,255,0.03)'}
                    onMouseOut={r => r.currentTarget.style.background = 'transparent'}
                  >
                    <td style={{ padding: '11px 16px' }}><span style={{ fontFamily: 'monospace', fontSize: 10, color: 'var(--cyan)' }}>{s.session_id}</span></td>
                    <td style={{ padding: '11px 16px' }}><span style={{ fontFamily: 'monospace', fontSize: 11, color: 'var(--text)' }}>{s.ip_address}</span></td>
                    <td style={{ padding: '11px 16px' }}><span style={{ fontFamily: 'monospace', fontSize: 11, color: 'var(--text2)' }}>{formatTime(s.login_time)}</span></td>
                    <td style={{ padding: '11px 16px' }}>
                      {s.status === 'ACTIVE'
                        ? <span style={{ fontFamily: 'monospace', fontSize: 11, color: 'var(--green)' }}>— online —</span>
                        : <span style={{ fontFamily: 'monospace', fontSize: 11, color: 'var(--text2)' }}>{formatTime(s.logout_time)}</span>
                      }
                    </td>
                    <td style={{ padding: '11px 16px' }}><span style={{ fontFamily: 'monospace', fontSize: 11, color: 'var(--text2)' }}>{formatDuration(s.login_time, s.logout_time)}</span></td>
                    <td style={{ padding: '11px 16px' }}><span style={{ fontFamily: 'monospace', fontSize: 11, color: 'var(--text2)' }}>{formatBytes(s.traffic_bytes)}</span></td>
                    <td style={{ padding: '11px 16px' }}>
                      {s.status === 'ACTIVE'
                        ? <span className="badge b-green">ACTIVE</span>
                        : <span className="badge b-log">ENDED</span>
                      }
                    </td>
                  </tr>
                ))
            }
          </tbody>
        </table>

        {totalPages > 1 && (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '14px 18px', borderTop: '1px solid var(--border)', gap: 4 }}>
            <button onClick={() => setPage(p => Math.max(1, p-1))} disabled={page===1} style={{ width:30,height:30,borderRadius:6,border:'1px solid var(--border)',background:'transparent',color:'var(--text2)',cursor:page===1?'not-allowed':'pointer',opacity:page===1?0.3:1,display:'flex',alignItems:'center',justifyContent:'center' }}>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="15 18 9 12 15 6"/></svg>
            </button>
            {Array.from({length:totalPages},(_,i)=>i+1).map(p=>(
              <button key={p} onClick={()=>setPage(p)} style={{ width:30,height:30,borderRadius:6,border:`1px solid ${p===page?'rgba(34,211,238,0.3)':'var(--border)'}`,background:p===page?'var(--cyan-dim)':'transparent',color:p===page?'var(--cyan)':'var(--text2)',cursor:'pointer',fontFamily:'var(--font)',fontSize:11,fontWeight:600,display:'flex',alignItems:'center',justifyContent:'center' }}>{p}</button>
            ))}
            <button onClick={()=>setPage(p=>Math.min(totalPages,p+1))} disabled={page===totalPages} style={{ width:30,height:30,borderRadius:6,border:'1px solid var(--border)',background:'transparent',color:'var(--text2)',cursor:page===totalPages?'not-allowed':'pointer',opacity:page===totalPages?0.3:1,display:'flex',alignItems:'center',justifyContent:'center' }}>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="9 18 15 12 9 6"/></svg>
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
