import { useState, useRef, useEffect } from 'react'
import { api } from '../api'
import EventModal from '../components/EventModal'

const RISK_CLASS = { LOW:'b-low', MEDIUM:'b-medium', HIGH:'b-high', CRITICAL:'b-critical' }
const STATUS_MAP = {
  TEMP_BLOCK: { label:'Blocked',  cls:'b-critical' },
  RATE_LIMIT: { label:'Active',   cls:'b-high' },
  MONITOR:    { label:'Watching', cls:'b-monitor' },
  LOG:        { label:'Logged',   cls:'b-log' },
}
const riskOrder = { CRITICAL:0, HIGH:1, MEDIUM:2, LOW:3 }

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

export default function EventsPage() {
  const [events, setEvents] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [sortKey, setSortKey] = useState('')
  const [sortOpen, setSortOpen] = useState(false)
  const [selected, setSelected] = useState(null)
  const sortRef = useRef(null)

  async function fetchEvents() {
    try {
      const data = await api.getEvents({ limit: 1000 })
      setEvents(data)
    } catch (e) {
      console.error('Events API error:', e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchEvents()
    const t = setInterval(fetchEvents, 10000)
    return () => clearInterval(t)
  }, [])

  useEffect(() => {
    function handler(e) { if (sortRef.current && !sortRef.current.contains(e.target)) setSortOpen(false) }
    document.addEventListener('click', handler)
    return () => document.removeEventListener('click', handler)
  }, [])

  function doSort(key) {
    setSortKey(key)
    setSortOpen(false)
    setEvents(prev => {
      const arr = [...prev]
      if (key === 'evtid') arr.sort((a,b) => b.event_id.localeCompare(a.event_id))
      if (key === 'risk')  arr.sort((a,b) => (riskOrder[a.risk_level]??99) - (riskOrder[b.risk_level]??99))
      if (key === 'time')  arr.sort((a,b) => new Date(b.timestamp) - new Date(a.timestamp))
      return arr
    })
  }

  const filtered = events.filter(e => {
    return matchesSearch([
      e.source_ip,
      e.event_id,
      e.risk_level,
      e.action_taken,
      e.timestamp,
    ], search)
  })

  return (
    <div style={{ padding: 20 }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 20 }}>
        <div style={{ width: 36, height: 36, borderRadius: 8, background: 'var(--cyan-dim)', color: 'var(--cyan)', border: '1px solid rgba(34,211,238,0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
        </div>
        <div>
          <div style={{ fontSize: 18, fontWeight: 700 }}>Event Log</div>
          <div style={{ fontSize: 11, color: 'var(--text2)' }}>Real-time IDS/IPS event monitoring and analysis</div>
        </div>
      </div>

      {/* Search */}
      <div style={{ position: 'relative', marginBottom: 12 }}>
        <span style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text3)', display: 'flex', pointerEvents: 'none' }}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
        </span>
        <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search by Event ID or Source IP..."
          style={{ width: '100%', background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 8, padding: '9px 14px 9px 36px', color: 'var(--text)', fontSize: 12, fontFamily: 'var(--font)', outline: 'none' }}
          onFocus={e => e.target.style.borderColor='rgba(34,211,238,0.3)'}
          onBlur={e => e.target.style.borderColor='var(--border)'}
        />
      </div>

      {/* Sort */}
      <div style={{ position: 'relative', marginBottom: 12 }} ref={sortRef}>
        <button onClick={() => setSortOpen(o => !o)} style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '5px 14px', borderRadius: 6, fontSize: 11, fontWeight: 600, background: 'var(--cyan)', color: '#0d1117', border: '1px solid var(--cyan)', cursor: 'pointer', fontFamily: 'var(--font)' }}>
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><line x1="3" y1="6" x2="21" y2="6"/><line x1="6" y1="12" x2="18" y2="12"/><line x1="9" y1="18" x2="15" y2="18"/></svg>
          Sort by
        </button>
        {sortOpen && (
          <div style={{ position: 'absolute', top: 'calc(100% + 6px)', left: 0, background: '#1e2a3a', border: '1px solid var(--border2)', borderRadius: 8, minWidth: 150, zIndex: 50, boxShadow: '0 8px 24px rgba(0,0,0,0.4)', overflow: 'hidden' }}>
            {[
              { key:'evtid', label:'Event ID' },
              { key:'risk',  label:'Risk' },
              { key:'time',  label:'Time' },
            ].map(({ key, label }) => (
              <div key={key} onClick={() => doSort(key)}
                style={{ padding: '10px 14px', fontSize: 12, color: sortKey===key ? 'var(--cyan)' : 'var(--text2)', cursor: 'pointer', background: sortKey===key ? 'var(--cyan-dim)' : 'transparent' }}
                onMouseOver={e => { e.currentTarget.style.background='var(--cyan-dim)'; e.currentTarget.style.color='var(--cyan)' }}
                onMouseOut={e => { if(sortKey!==key){ e.currentTarget.style.background='transparent'; e.currentTarget.style.color='var(--text2)' } }}>
                {label}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Table */}
      <div style={{ background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 10, overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr>
              {['Event ID','Time','Source IP','Risk','Stability','Load','Status','Details'].map(h => (
                <th key={h} style={{ padding: '10px 16px', textAlign: 'left', fontSize: 9, fontWeight: 600, letterSpacing: 1, textTransform: 'uppercase', color: 'var(--text3)', background: 'rgba(255,255,255,0.02)', borderBottom: '1px solid var(--border)' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading
              ? <tr><td colSpan={8} style={{ textAlign: 'center', padding: 30, color: 'var(--text3)', fontSize: 12 }}>Loading...</td></tr>
              : filtered.length === 0
                ? <tr><td colSpan={8} style={{ textAlign: 'center', padding: 30, color: 'var(--text3)', fontSize: 12 }}>No events found</td></tr>
                : filtered.map(ev => {
                  const st = STATUS_MAP[ev.action_taken] || { label: ev.action_taken, cls: 'b-log' }
                  const time = new Date(ev.timestamp).toTimeString().slice(0,8)
                  return (
                    <tr key={ev.event_id} style={{ borderBottom: '1px solid rgba(255,255,255,0.03)', transition: 'background 0.1s' }}
                      onMouseOver={e => e.currentTarget.style.background='rgba(255,255,255,0.03)'}
                      onMouseOut={e => e.currentTarget.style.background='transparent'}>
                      <td style={{ padding: '11px 16px' }}><span className="evtid-mono">{ev.event_id}</span></td>
                      <td style={{ padding: '11px 16px' }}><span className="time-mono">{time}</span></td>
                      <td style={{ padding: '11px 16px' }}><span className="ip-mono">{ev.source_ip}</span></td>
                      <td style={{ padding: '11px 16px' }}><span className={`badge ${RISK_CLASS[ev.risk_level]||'b-log'}`}>{ev.risk_level}</span></td>
                      <td style={{ padding: '11px 16px', color: 'var(--text2)', fontSize: 12 }}>{(ev.stability_score??0).toFixed(2)}</td>
                      <td style={{ padding: '11px 16px', color: 'var(--text2)', fontSize: 12 }}>{(ev.network_load??0).toFixed(2)}</td>
                      <td style={{ padding: '11px 16px' }}><span className={`badge ${st.cls}`}>{st.label}</span></td>
                      <td style={{ padding: '11px 16px' }}>
                        <button onClick={() => setSelected(ev)} style={{ padding: '4px 10px', borderRadius: 5, fontSize: 10, fontWeight: 600, background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border)', color: 'var(--text2)', cursor: 'pointer', fontFamily: 'var(--font)', transition: 'all 0.15s' }}
                          onMouseOver={e => { e.currentTarget.style.background='var(--cyan-dim)'; e.currentTarget.style.color='var(--cyan)'; e.currentTarget.style.borderColor='rgba(34,211,238,0.2)' }}
                          onMouseOut={e => { e.currentTarget.style.background='rgba(255,255,255,0.05)'; e.currentTarget.style.color='var(--text2)'; e.currentTarget.style.borderColor='var(--border)' }}>
                          View
                        </button>
                      </td>
                    </tr>
                  )
                })
            }
          </tbody>
        </table>
      </div>

      {selected && <EventModal event={selected} onClose={() => setSelected(null)} />}
    </div>
  )
}
