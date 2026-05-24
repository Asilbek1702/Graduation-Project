import { useEffect, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'

const RISK_COLORS = { CRITICAL: 'var(--red)', HIGH: 'var(--orange)', MEDIUM: 'var(--yellow)', LOW: 'var(--green)' }
const CW = 720, CH = 155, PAD_L = 52

function niceMax(val) {
  if (val === 0) return 10
  const mag = Math.pow(10, Math.floor(Math.log10(val)))
  const n = val / mag
  const nice = n <= 1 ? 1 : n <= 2 ? 2 : n <= 5 ? 5 : 10
  return nice * mag
}

function toY(v, maxVal) {
  if (maxVal === 0) return CH
  return CH - Math.round((v / maxVal) * (CH - 18))
}

function buildLine(data, maxVal) {
  if (!data || data.length < 2) return ''
  const step = (CW - PAD_L) / (data.length - 1)
  return data.map((v, i) => `${PAD_L + i * step},${toY(v, maxVal)}`).join(' ')
}

function buildArea(data, maxVal) {
  if (!data || data.length < 2) return ''
  const step = (CW - PAD_L) / (data.length - 1)
  const pts  = data.map((v, i) => `${PAD_L + i * step},${toY(v, maxVal)}`)
  return `M${PAD_L},${CH} L${pts.join(' L')} L${PAD_L + (data.length - 1) * step},${CH} Z`
}

export default function DashboardPage() {
  const [stats, setStats]         = useState(null)
  const [recentEvents, setRecent] = useState([])
  const [chartData, setChart]     = useState(null)
  const [period, setPeriod]       = useState('24h')
  const [loading, setLoading]     = useState(true)
  const nav = useNavigate()

  const fetchAll = useCallback(async () => {
    try {
      const [s, evts, chart] = await Promise.all([
        api.getStats(),
        api.getEvents({ limit: 4 }),
        api.getChartData(period),
      ])
      setStats(s); setRecent(evts); setChart(chart)
    } catch (e) { console.error(e) }
    finally { setLoading(false) }
  }, [period])

  useEffect(() => {
    setLoading(true); fetchAll()
    const t = setInterval(fetchAll, 15000)
    return () => clearInterval(t)
  }, [fetchAll])

  const totalFlows  = stats ? (stats.total_flows || 0).toLocaleString() : '—'
  const blockedIPs  = stats ? (stats.blocked_ips ?? '—') : '—'
  const networkLoad = stats ? Math.round((stats.current_network_load || 0) * 100) + '%' : '—'
  const loadColor   = !stats ? 'var(--green)' : stats.current_network_load > 0.7 ? 'var(--orange)' : stats.current_network_load > 0.3 ? 'var(--yellow)' : 'var(--green)'

  const userVals  = chartData?.unique_ips  || []
  const blockVals = chartData?.blocked_ips || []
  const labels    = chartData?.labels      || []
  const rawMax    = Math.max(...userVals, ...blockVals, 0)
  const maxVal    = niceMax(rawMax)

  const yTicks = [maxVal, Math.round(maxVal * 0.75), Math.round(maxVal * 0.5), Math.round(maxVal * 0.25), 0]
  const yPos   = [18, 51, 88, 121, CH]

  const step   = labels.length > 1 ? (CW - PAD_L) / (labels.length - 1) : 0
  const pUIdx  = userVals.indexOf(Math.max(...userVals, 0))
  const pBIdx  = blockVals.indexOf(Math.max(...blockVals, 0))
  const isEmpty = userVals.every(v => v === 0) && blockVals.every(v => v === 0)

  return (
    <div style={{ padding: 20 }}>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 14, marginBottom: 18 }}>
        <StatCard onClick={() => nav('/events')} label="TOTAL FLOWS" value={loading ? '...' : totalFlows} valueColor="var(--text)" iconColor="var(--cyan)" iconBg="var(--cyan-dim)" icon={<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>}/>
        <StatCard onClick={() => nav('/blocked')} label="BLOCKED IPS" value={loading ? '...' : blockedIPs} valueColor="var(--red)" iconColor="var(--red)" iconBg="var(--red-dim)" icon={<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>}/>
        <StatCard label="NETWORK LOAD" value={loading ? '...' : networkLoad} valueColor={loadColor} iconColor="var(--green)" iconBg="var(--green-dim)" icon={<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M5 12.55a11 11 0 0 1 14.08 0"/><path d="M1.42 9a16 16 0 0 1 21.16 0"/><path d="M8.53 16.11a6 6 0 0 1 6.95 0"/><line x1="12" y1="20" x2="12.01" y2="20"/></svg>}/>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 300px', gap: 14, marginBottom: 18 }}>
        {/* Chart */}
        <div style={{ background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 10, padding: '18px 20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
            <div style={{ fontSize: 13, fontWeight: 600 }}>Active Users vs Blocked IPs over Time</div>
            <div style={{ display: 'flex', gap: 6 }}>
              {['24h','7d'].map(p => (
                <button key={p} onClick={() => setPeriod(p)} style={{ padding: '4px 12px', borderRadius: 5, fontSize: 11, fontWeight: 600, cursor: 'pointer', fontFamily: 'var(--font)', background: period===p ? 'var(--cyan)' : 'transparent', color: period===p ? '#0d1117' : 'var(--text2)', border: period===p ? '1px solid var(--cyan)' : '1px solid var(--border2)' }}>{p}</button>
              ))}
            </div>
          </div>

          {loading || !chartData ? (
            <div style={{ height: 185, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text3)', fontSize: 12 }}>Loading chart data...</div>
          ) : isEmpty ? (
            <div style={{ height: 185, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text3)', fontSize: 12 }}>No data for this period yet</div>
          ) : (
            <svg width="100%" viewBox="0 0 720 190" preserveAspectRatio="none" style={{ height: 190, overflow: 'visible' }}>
              <defs>
                <linearGradient id="cg" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#22d3ee" stopOpacity="0.2"/><stop offset="100%" stopColor="#22d3ee" stopOpacity="0"/></linearGradient>
                <linearGradient id="rg" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#ef4444" stopOpacity="0.25"/><stop offset="100%" stopColor="#ef4444" stopOpacity="0"/></linearGradient>
              </defs>
              {yPos.slice(0,-1).map(y => <line key={y} stroke="rgba(255,255,255,0.04)" strokeWidth="1" x1={PAD_L} y1={y} x2={CW} y2={y}/>)}
              <line stroke="rgba(255,255,255,0.08)" strokeWidth="1" x1={PAD_L} y1="10" x2={PAD_L} y2={CH}/>
              <line stroke="rgba(255,255,255,0.08)" strokeWidth="1" x1={PAD_L} y1={CH} x2={CW} y2={CH}/>
              {yTicks.map((v,i) => <text key={i} fontSize="9" fill="#4b5563" fontFamily="Inter,sans-serif" x={PAD_L-4} y={yPos[i]+4} textAnchor="end">{v>=1000?`${v/1000}k`:v}</text>)}
              {labels.map((label,i) => <text key={i} fontSize="9" fill="#4b5563" fontFamily="Inter,sans-serif" x={PAD_L+i*step} y="172" textAnchor="middle">{label}</text>)}
              {buildArea(userVals, maxVal)  && <path d={buildArea(userVals, maxVal)}  fill="url(#cg)"/>}
              {buildArea(blockVals, maxVal) && <path d={buildArea(blockVals, maxVal)} fill="url(#rg)"/>}
              {buildLine(userVals, maxVal)  && <polyline points={buildLine(userVals, maxVal)}  fill="none" stroke="#22d3ee" strokeWidth="2" strokeLinejoin="round"/>}
              {buildLine(blockVals, maxVal) && <polyline points={buildLine(blockVals, maxVal)} fill="none" stroke="#ef4444" strokeWidth="2" strokeLinejoin="round"/>}
              {userVals[pUIdx]  > 0 && <circle cx={PAD_L+pUIdx*step}  cy={toY(userVals[pUIdx], maxVal)}  r="3.5" fill="#22d3ee"/>}
              {blockVals[pBIdx] > 0 && <circle cx={PAD_L+pBIdx*step}  cy={toY(blockVals[pBIdx], maxVal)} r="3.5" fill="#ef4444"/>}
            </svg>
          )}
          <div style={{ display: 'flex', gap: 18, marginTop: 12, fontSize: 11, color: 'var(--text2)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}><span style={{ display: 'inline-block', width: 24, height: 2, background: '#22d3ee', borderRadius: 1 }}/> Total users online</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}><span style={{ display: 'inline-block', width: 24, height: 2, background: '#ef4444', borderRadius: 1 }}/> Blocked IPs</div>
          </div>
        </div>

        {/* Recent Events */}
        <div style={{ background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 10, padding: '18px 20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, fontWeight: 600, marginBottom: 14, color: 'var(--red)' }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
            Recent Events
          </div>
          {loading ? <div style={{ color: 'var(--text3)', fontSize: 12 }}>Loading...</div>
            : recentEvents.length === 0 ? <div style={{ color: 'var(--text3)', fontSize: 12 }}>No events yet</div>
            : recentEvents.map((e, i) => {
              const color = RISK_COLORS[e.risk_level] || 'var(--text2)'
              return (
                <div key={e.event_id} style={{ display: 'flex', alignItems: 'flex-start', gap: 10, padding: '8px 0', borderBottom: i < recentEvents.length-1 ? '1px solid var(--border)' : 'none' }}>
                  <div style={{ width: 7, height: 7, borderRadius: '50%', background: color, marginTop: 4, flexShrink: 0 }}/>
                  <div>
                    <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text)', fontFamily: 'monospace' }}>{e.source_ip}</div>
                    <div style={{ fontSize: 10, color: 'var(--text3)', marginTop: 2 }}>{new Date(e.timestamp).toTimeString().slice(0,8)} · <span style={{ color, fontWeight: 600 }}>{e.risk_level}</span> · {e.action_taken}</div>
                  </div>
                </div>
              )
            })
          }
        </div>
      </div>

      {/* Protocol Mix */}
      <div style={{ background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 10, padding: '18px 20px' }}>
        <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 14 }}>Protocol Mix</div>
        {stats?.protocol_distribution
          ? Object.entries(stats.protocol_distribution).map(([name, count], i, arr) => {
            const total = Object.values(stats.protocol_distribution).reduce((a,b)=>a+b,0)
            const pct   = total ? Math.round(count/total*100) : 0
            const color = name==='TCP' ? '#22d3ee' : name==='UDP' ? '#a78bfa' : '#f97316'
            return (
              <div key={name} style={{ display:'flex', alignItems:'center', padding:'8px 0', borderBottom: i<arr.length-1?'1px solid var(--border)':'none', fontSize:12 }}>
                <div style={{ width:8,height:8,borderRadius:'50%',background:color,marginRight:10 }}/>
                <div style={{ flex:1,color:'var(--text2)' }}>{name}</div>
                <div style={{ flex:2,height:4,background:'rgba(255,255,255,0.05)',borderRadius:2,margin:'0 14px' }}>
                  <div style={{ height:'100%',borderRadius:2,background:color,width:`${pct}%` }}/>
                </div>
                <div style={{ fontSize:11,color:'var(--text2)',minWidth:100,textAlign:'right' }}>{pct}% ({count.toLocaleString()})</div>
              </div>
            )
          })
          : <div style={{ color:'var(--text3)',fontSize:12 }}>{loading?'Loading...':'No protocol data yet'}</div>
        }
      </div>
    </div>
  )
}

function StatCard({ onClick, label, value, valueColor, icon, iconColor, iconBg }) {
  return (
    <div onClick={onClick} style={{ background:'var(--card)',border:'1px solid var(--border)',borderRadius:10,padding:'16px 18px',display:'flex',alignItems:'flex-start',justifyContent:'space-between',cursor:onClick?'pointer':'default',transition:'all 0.2s' }}
      onMouseOver={e=>{if(onClick){e.currentTarget.style.borderColor='var(--border2)';e.currentTarget.style.transform='translateY(-1px)'}}}
      onMouseOut={e=>{e.currentTarget.style.borderColor='var(--border)';e.currentTarget.style.transform='translateY(0)'}}>
      <div>
        <div style={{ fontSize:10,fontWeight:600,letterSpacing:1,textTransform:'uppercase',color:'var(--text2)',marginBottom:10 }}>{label}</div>
        <div style={{ fontSize:28,fontWeight:700,color:valueColor||'var(--text)',lineHeight:1 }}>{value}</div>
      </div>
      <div style={{ width:36,height:36,borderRadius:8,background:iconBg,color:iconColor,display:'flex',alignItems:'center',justifyContent:'center',flexShrink:0 }}>{icon}</div>
    </div>
  )
}