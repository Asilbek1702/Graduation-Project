import { useState, useEffect } from 'react'
import { api } from '../api'
import { useToast } from '../hooks/useToast'

const RISK_CLASS = { CRITICAL:'b-critical', HIGH:'b-high', MEDIUM:'b-medium', LOW:'b-low' }

export default function BlockedPage() {
  const [list, setList] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const showToast = useToast()

  async function fetchBlocked() {
    try {
      const data = await api.getBlocked()
      setList(data)
    } catch (e) {
      console.error('Blocked API error:', e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchBlocked()
    const t = setInterval(fetchBlocked, 10000)
    return () => clearInterval(t)
  }, [])

  async function handleUnblock(ip) {
    try {
      await api.unblockIP(ip)
      showToast(`IP ${ip} has been unblocked`, '#22d3ee')
      fetchBlocked()
    } catch (e) {
      showToast(`Failed to unblock ${ip}`, '#ef4444')
    }
  }

  const filtered = list.filter(b => !search || b.ip_address.includes(search))
  const highRisk = list.filter(b => b.risk_level === 'CRITICAL' || b.risk_level === 'HIGH').length

  function formatTime(iso) {
    if (!iso) return '—'
    try { return new Date(iso).toTimeString().slice(0,8) } catch { return iso }
  }

  return (
    <div style={{ padding: 20 }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 20 }}>
        <div style={{ width: 36, height: 36, borderRadius: 8, background: 'var(--red-dim)', color: 'var(--red)', border: '1px solid rgba(239,68,68,0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
        </div>
        <div>
          <div style={{ fontSize: 18, fontWeight: 700 }}>Blocked IP Addresses</div>
          <div style={{ fontSize: 11, color: 'var(--text2)' }}>Manage blocked hosts and security restrictions</div>
        </div>
      </div>

      {/* Search */}
      <div style={{ position: 'relative', marginBottom: 16 }}>
        <span style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text3)', display: 'flex', pointerEvents: 'none' }}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
        </span>
        <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search by IP address..."
          style={{ width: '100%', background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 8, padding: '9px 14px 9px 36px', color: 'var(--text)', fontSize: 12, fontFamily: 'var(--font)', outline: 'none' }}
          onFocus={e => e.target.style.borderColor='rgba(34,211,238,0.3)'}
          onBlur={e => e.target.style.borderColor='var(--border)'}
        />
      </div>

      {/* Stats */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14, marginBottom: 18 }}>
        <div style={{ background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 10, padding: '18px 20px' }}>
          <div style={{ fontSize: 11, color: 'var(--text2)', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
            Total Blocked
          </div>
          <div style={{ fontSize: 28, fontWeight: 700 }}>{loading ? '...' : list.length}</div>
        </div>
        <div style={{ background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 10, padding: '18px 20px' }}>
          <div style={{ fontSize: 11, color: 'var(--orange)', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
            High Risk
          </div>
          <div style={{ fontSize: 28, fontWeight: 700, color: 'var(--orange)' }}>{loading ? '...' : highRisk}</div>
        </div>
      </div>

      {/* Table */}
      <div style={{ background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 10, overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr>
              {['IP Address','Blocked At','Expires At','Strike Count','Risk Level','Action'].map(h => (
                <th key={h} style={{ padding: '10px 16px', textAlign: 'left', fontSize: 9, fontWeight: 600, letterSpacing: 1, textTransform: 'uppercase', color: 'var(--text3)', background: 'rgba(255,255,255,0.02)', borderBottom: '1px solid var(--border)' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading
              ? <tr><td colSpan={6} style={{ textAlign: 'center', padding: 30, color: 'var(--text3)', fontSize: 12 }}>Loading...</td></tr>
              : filtered.length === 0
                ? <tr><td colSpan={6} style={{ textAlign: 'center', padding: 30, color: 'var(--text3)', fontSize: 12 }}>No blocked IPs</td></tr>
                : filtered.map(b => (
                  <tr key={b.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.03)', transition: 'background 0.1s' }}
                    onMouseOver={e => e.currentTarget.style.background='rgba(255,255,255,0.03)'}
                    onMouseOut={e => e.currentTarget.style.background='transparent'}>
                    <td style={{ padding: '11px 16px' }}><span className="ip-mono">{b.ip_address}</span></td>
                    <td style={{ padding: '11px 16px' }}><span className="time-mono">{formatTime(b.blocked_at)}</span></td>
                    <td style={{ padding: '11px 16px' }}><span className="time-mono">{formatTime(b.block_expires_at)}</span></td>
                    <td style={{ padding: '11px 16px', color: 'var(--text2)', fontSize: 12 }}>{b.strike_count}</td>
                    <td style={{ padding: '11px 16px' }}><span className={`badge ${RISK_CLASS[b.risk_level]||'b-high'}`}>{b.risk_level}</span></td>
                    <td style={{ padding: '11px 16px' }}>
                      <button onClick={() => handleUnblock(b.ip_address)} style={{ padding: '5px 12px', borderRadius: 6, fontSize: 10, fontWeight: 600, background: 'var(--cyan-dim)', border: '1px solid rgba(34,211,238,0.25)', color: 'var(--cyan)', cursor: 'pointer', fontFamily: 'var(--font)', transition: 'all 0.15s' }}
                        onMouseOver={e => e.currentTarget.style.background='rgba(34,211,238,0.2)'}
                        onMouseOut={e => e.currentTarget.style.background='var(--cyan-dim)'}>
                        Unblock
                      </button>
                    </td>
                  </tr>
                ))
            }
          </tbody>
        </table>
      </div>
    </div>
  )
}
