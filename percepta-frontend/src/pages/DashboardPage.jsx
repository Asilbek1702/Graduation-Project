import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'

const chartData = {
  '24h': {
    usersArea: "M52,152 L90,149 L134,146 L180,142 L216,125 L260,96 L298,68 L340,50 L380,42 L420,46 L462,55 L500,70 L544,90 L580,112 L626,134 L668,146 L715,152 L715,155 L52,155 Z",
    usersLine: "M52,152 L90,149 L134,146 L180,142 L216,125 L260,96 L298,68 L340,50 L380,42 L420,46 L462,55 L500,70 L544,90 L580,112 L626,134 L668,146 L715,152",
    blockedArea: "M52,155 L134,155 L180,154 L216,153 L260,151 L298,148 L340,146 L380,144 L420,145 L462,147 L500,150 L544,152 L580,153 L668,155 L715,155",
    blockedLine: "M52,155 L134,155 L180,154 L216,153 L260,151 L298,148 L340,146 L380,144 L420,145 L462,147 L500,150 L544,152 L580,153 L668,155 L715,155",
    xLabels: ['00:00','03:00','06:00','09:00','12:00','15:00','18:00','21:00','24:00'],
    peakU: { cx: 380, cy: 42 }, peakB: { cx: 380, cy: 144 }
  },
  '7d': {
    usersArea: "M52,148 L134,138 L216,118 L298,88 L380,55 L462,72 L544,98 L626,128 L715,148 L715,155 L52,155 Z",
    usersLine: "M52,148 L134,138 L216,118 L298,88 L380,55 L462,72 L544,98 L626,128 L715,148",
    blockedArea: "M52,154 L134,153 L216,150 L298,145 L380,138 L462,142 L544,148 L626,152 L715,154",
    blockedLine: "M52,154 L134,153 L216,150 L298,145 L380,138 L462,142 L544,148 L626,152 L715,154",
    xLabels: ['Mon','Tue','Wed','Thu','Fri','Sat','Sun','',''],
    peakU: { cx: 380, cy: 55 }, peakB: { cx: 380, cy: 138 }
  }
}

const RISK_COLORS = { CRITICAL:'var(--red)', HIGH:'var(--orange)', MEDIUM:'var(--yellow)', LOW:'var(--green)' }

export default function DashboardPage() {
  const [stats, setStats] = useState(null)
  const [recentEvents, setRecentEvents] = useState([])
  const [period, setPeriod] = useState('24h')
  const [loading, setLoading] = useState(true)
  const nav = useNavigate()

  async function fetchData() {
    try {
      const [s, evts] = await Promise.all([
        api.getStats(),
        api.getEvents({ limit: 4 })
      ])
      setStats(s)
      setRecentEvents(evts)
    } catch (e) {
      console.error('API error:', e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
    const t = setInterval(fetchData, 15000)
    return () => clearInterval(t)
  }, [])

  const d = chartData[period]
  const totalFlows = stats ? (stats.total_flows || 0).toLocaleString() : '—'
  const blockedIPs = stats ? (stats.blocked_ips ?? '—') : '—'
  const networkLoad = stats ? Math.round((stats.current_network_load || 0) * 100) + '%' : '—'
  const loadColor = stats
    ? (stats.current_network_load > 0.7 ? 'var(--orange)' : stats.current_network_load > 0.3 ? 'var(--yellow)' : 'var(--green)')
    : 'var(--green)'

  return (
    <div style={{ padding: 20 }}>
      {/* Stat Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 14, marginBottom: 18 }}>
        <div onClick={() => nav('/events')} style={{ background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 10, padding: '16px 18px', display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', cursor: 'pointer', transition: 'all 0.2s' }}
          onMouseOver={e => { e.currentTarget.style.borderColor='var(--border2)'; e.currentTarget.style.transform='translateY(-1px)' }}
          onMouseOut={e => { e.currentTarget.style.borderColor='var(--border)'; e.currentTarget.style.transform='translateY(0)' }}>
          <div>
            <div style={{ fontSize: 10, fontWeight: 600, letterSpacing: 1, textTransform: 'uppercase', color: 'var(--text2)', marginBottom: 10 }}>TOTAL FLOWS</div>
            <div style={{ fontSize: 28, fontWeight: 700, color: 'var(--text)', lineHeight: 1 }}>{loading ? '...' : totalFlows}</div>
          </div>
          <div style={{ width: 36, height: 36, borderRadius: 8, background: 'var(--cyan-dim)', color: 'var(--cyan)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
          </div>
        </div>

        <div onClick={() => nav('/blocked')} style={{ background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 10, padding: '16px 18px', display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', cursor: 'pointer', transition: 'all 0.2s' }}
          onMouseOver={e => { e.currentTarget.style.borderColor='var(--border2)'; e.currentTarget.style.transform='translateY(-1px)' }}
          onMouseOut={e => { e.currentTarget.style.borderColor='var(--border)'; e.currentTarget.style.transform='translateY(0)' }}>
          <div>
            <div style={{ fontSize: 10, fontWeight: 600, letterSpacing: 1, textTransform: 'uppercase', color: 'var(--text2)', marginBottom: 10 }}>BLOCKED IPS</div>
            <div style={{ fontSize: 28, fontWeight: 700, color: 'var(--red)', lineHeight: 1 }}>{loading ? '...' : blockedIPs}</div>
          </div>
          <div style={{ width: 36, height: 36, borderRadius: 8, background: 'var(--red-dim)', color: 'var(--red)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
          </div>
        </div>

        <div style={{ background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 10, padding: '16px 18px', display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
          <div>
            <div style={{ fontSize: 10, fontWeight: 600, letterSpacing: 1, textTransform: 'uppercase', color: 'var(--text2)', marginBottom: 10 }}>NETWORK LOAD</div>
            <div style={{ fontSize: 28, fontWeight: 700, color: loadColor, lineHeight: 1 }}>{loading ? '...' : networkLoad}</div>
          </div>
          <div style={{ width: 36, height: 36, borderRadius: 8, background: 'var(--green-dim)', color: 'var(--green)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M5 12.55a11 11 0 0 1 14.08 0"/><path d="M1.42 9a16 16 0 0 1 21.16 0"/><path d="M8.53 16.11a6 6 0 0 1 6.95 0"/><line x1="12" y1="20" x2="12.01" y2="20"/></svg>
          </div>
        </div>
      </div>

      {/* Chart + Recent Events */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 300px', gap: 14, marginBottom: 18 }}>
        <div style={{ background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 10, padding: '18px 20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
            <div style={{ fontSize: 13, fontWeight: 600 }}>Active Users vs Blocked IPs over Time</div>
            <div style={{ display: 'flex', gap: 6 }}>
              {['24h','7d'].map(p => (
                <button key={p} onClick={() => setPeriod(p)} style={{ padding: '4px 12px', borderRadius: 5, fontSize: 11, fontWeight: 600, cursor: 'pointer', fontFamily: 'var(--font)', transition: 'all 0.15s', background: period===p ? 'var(--cyan)' : 'transparent', color: period===p ? '#0d1117' : 'var(--text2)', border: period===p ? '1px solid var(--cyan)' : '1px solid var(--border2)' }}>{p}</button>
              ))}
            </div>
          </div>
          <svg width="100%" viewBox="0 0 720 185" preserveAspectRatio="none" style={{ height: 185, overflow: 'visible' }}>
            <defs>
              <linearGradient id="cg" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#22d3ee" stopOpacity="0.2"/><stop offset="100%" stopColor="#22d3ee" stopOpacity="0"/></linearGradient>
              <linearGradient id="rg" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#ef4444" stopOpacity="0.25"/><stop offset="100%" stopColor="#ef4444" stopOpacity="0"/></linearGradient>
            </defs>
            {[18,55,92,129].map(y => <line key={y} stroke="rgba(255,255,255,0.04)" strokeWidth="1" x1="52" y1={y} x2="715" y2={y}/>)}
            <line stroke="rgba(255,255,255,0.08)" strokeWidth="1" x1="52" y1="10" x2="52" y2="155"/>
            <line stroke="rgba(255,255,255,0.08)" strokeWidth="1" x1="52" y1="155" x2="715" y2="155"/>
            {[['2000',22],['1500',59],['1000',96],['500',133],['0',158]].map(([v,y]) => (
              <text key={y} fontSize="9" fill="#4b5563" fontFamily="Inter,sans-serif" x="48" y={y} textAnchor="end">{v}</text>
            ))}
            {[52,134,216,298,380,462,544,626,708].map((x,i) => (
              <text key={i} fontSize="9" fill="#4b5563" fontFamily="Inter,sans-serif" x={x} y="170" textAnchor="middle">{d.xLabels[i]||''}</text>
            ))}
            <path d={d.usersArea} fill="url(#cg)"/>
            <path d={d.usersLine} fill="none" stroke="#22d3ee" strokeWidth="2" strokeLinejoin="round"/>
            <path d={d.blockedArea} fill="url(#rg)"/>
            <path d={d.blockedLine} fill="none" stroke="#ef4444" strokeWidth="2" strokeLinejoin="round"/>
            <circle cx={d.peakU.cx} cy={d.peakU.cy} r="3.5" fill="#22d3ee"/>
            <circle cx={d.peakB.cx} cy={d.peakB.cy} r="3.5" fill="#ef4444"/>
          </svg>
          <div style={{ display: 'flex', gap: 18, marginTop: 12, fontSize: 11, color: 'var(--text2)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}><span style={{ display: 'inline-block', width: 24, height: 2, background: '#22d3ee', borderRadius: 1 }}/> Total users online</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}><span style={{ display: 'inline-block', width: 24, height: 2, background: '#ef4444', borderRadius: 1 }}/> Blocked IPs</div>
          </div>
        </div>

        {/* Recent Events — real data */}
        <div style={{ background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 10, padding: '18px 20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, fontWeight: 600, marginBottom: 14, color: 'var(--red)' }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
            Recent Events
          </div>
          {loading
            ? <div style={{ color: 'var(--text3)', fontSize: 12 }}>Loading...</div>
            : recentEvents.length === 0
              ? <div style={{ color: 'var(--text3)', fontSize: 12 }}>No events yet</div>
              : recentEvents.map((e, i) => {
                const color = RISK_COLORS[e.risk_level] || 'var(--text2)'
                const time = new Date(e.timestamp).toTimeString().slice(0,8)
                return (
                  <div key={e.event_id} style={{ display: 'flex', alignItems: 'flex-start', gap: 10, padding: '8px 0', borderBottom: i < recentEvents.length-1 ? '1px solid var(--border)' : 'none' }}>
                    <div style={{ width: 7, height: 7, borderRadius: '50%', background: color, marginTop: 4, flexShrink: 0 }}/>
                    <div>
                      <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text)', fontFamily: 'monospace' }}>{e.source_ip}</div>
                      <div style={{ fontSize: 10, color: 'var(--text3)', marginTop: 2 }}>{time} · <span style={{ color, fontWeight: 600 }}>{e.risk_level}</span> · {e.action_taken}</div>
                    </div>
                  </div>
                )
              })
          }
        </div>
      </div>

      {/* Protocol Mix — real data */}
      <div style={{ background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 10, padding: '18px 20px' }}>
        <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 14 }}>Protocol Mix</div>
        {stats && stats.protocol_distribution
          ? Object.entries(stats.protocol_distribution).map(([name, count], i, arr) => {
            const total = Object.values(stats.protocol_distribution).reduce((a,b)=>a+b,0)
            const pct = total ? Math.round(count/total*100) : 0
            const color = name === 'TCP' ? '#22d3ee' : name === 'UDP' ? '#a78bfa' : '#f97316'
            return (
              <div key={name} style={{ display: 'flex', alignItems: 'center', padding: '8px 0', borderBottom: i<arr.length-1 ? '1px solid var(--border)' : 'none', fontSize: 12 }}>
                <div style={{ width: 8, height: 8, borderRadius: '50%', background: color, marginRight: 10 }}/>
                <div style={{ flex: 1, color: 'var(--text2)' }}>{name}</div>
                <div style={{ flex: 2, height: 4, background: 'rgba(255,255,255,0.05)', borderRadius: 2, margin: '0 14px' }}>
                  <div style={{ height: '100%', borderRadius: 2, background: color, width: `${pct}%` }}/>
                </div>
                <div style={{ fontSize: 11, color: 'var(--text2)', minWidth: 100, textAlign: 'right' }}>{pct}% ({count.toLocaleString()})</div>
              </div>
            )
          })
          : <div style={{ color: 'var(--text3)', fontSize: 12 }}>{loading ? 'Loading...' : 'No protocol data yet'}</div>
        }
      </div>
    </div>
  )
}
