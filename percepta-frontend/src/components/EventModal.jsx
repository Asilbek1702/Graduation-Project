import { useState } from 'react'

const riskColor = { LOW: 'var(--green)', MEDIUM: 'var(--yellow)', HIGH: 'var(--orange)', CRITICAL: 'var(--red)' }

function anomalyColor(v) { return v < 0.20 ? 'var(--red)' : v < 0.35 ? 'var(--orange)' : v < 0.50 ? 'var(--yellow)' : 'var(--green)' }
function stabColor(v)    { return v >= 0.75 ? 'var(--red)' : v >= 0.55 ? 'var(--orange)' : v >= 0.30 ? 'var(--yellow)' : 'var(--green)' }
function riskScoreColor(v){ return v >= 0.75 ? 'var(--red)' : v >= 0.50 ? 'var(--orange)' : v >= 0.30 ? 'var(--yellow)' : 'var(--green)' }
function loadColor(v)    { return v > 0.70 ? 'var(--orange)' : v > 0.30 ? 'var(--yellow)' : 'var(--green)' }
function formatDecimal(v) { return typeof v === 'number' ? v.toFixed(2) : v }

function Field({ label, value, color }) {
  return (
    <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border)', borderRadius: 7, padding: '10px 12px' }}>
      <div style={{ fontSize: 9, letterSpacing: 1, textTransform: 'uppercase', color: 'var(--text3)', marginBottom: 5 }}>{label}</div>
      <div style={{ fontSize: 13, fontWeight: 600, fontFamily: 'monospace', color: color || 'var(--text)' }}>{value ?? '—'}</div>
    </div>
  )
}

export default function EventModal({ event, onClose, onBlocked }) {
  const [blocking, setBlocking] = useState(false)
  const [blocked, setBlocked] = useState(false)
  const [blockError, setBlockError] = useState(null)

  if (!event) return null

  const actionLabel = event.action_duration_seconds > 0
    ? `${event.action_taken} · ${event.action_duration_seconds}s`
    : event.action_taken

  const isAlreadyBlocked = event.action_taken === 'TEMP_BLOCK' || blocked

  async function handleBlock() {
    if (blocking || isAlreadyBlocked) return
    setBlocking(true)
    setBlockError(null)
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/block/${event.source_ip}`, { method: 'POST' })
      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        throw new Error(data.detail || `HTTP ${res.status}`)
      }
      setBlocked(true)
      if (onBlocked) onBlocked(event.source_ip)
    } catch (e) {
      setBlockError(e.message || 'Failed to block IP')
    } finally {
      setBlocking(false)
    }
  }

  return (
    <div onClick={onClose} style={{
      position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.65)',
      backdropFilter: 'blur(3px)', zIndex: 200, display: 'flex', alignItems: 'center', justifyContent: 'center',
    }}>
      <div onClick={e => e.stopPropagation()} style={{
        background: '#161d2e', border: '1px solid rgba(34,211,238,0.2)',
        borderRadius: 12, width: 480, maxWidth: '95vw', padding: 22,
      }}>
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 18 }}>
          <div>
            <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--cyan)', fontFamily: 'monospace' }}>Event Details</div>
            <div style={{ fontSize: 10, color: 'var(--text3)', marginTop: 3, fontFamily: 'monospace' }}>{event.event_id}</div>
          </div>
          <button onClick={onClose} style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border)', borderRadius: 6, width: 26, height: 26, display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', color: 'var(--text2)', fontSize: 14 }}>✕</button>
        </div>

        {/* Fields */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 16 }}>
          <Field label="Source IP"         value={event.source_ip} />
          <Field label="Destination"       value={event.destination_ip ? `${event.destination_ip}:${event.destination_port ?? ''}` : '—'} />
          <Field label="Anomaly Score"     value={formatDecimal(event.anomaly_score)}        color={anomalyColor(event.anomaly_score)} />
          <Field label="Threshold"         value={formatDecimal(event.adaptive_threshold)} />
          <Field label="Stability Score"   value={formatDecimal(event.stability_score)}      color={stabColor(event.stability_score ?? 0)} />
          <Field label="Risk Score"        value={formatDecimal(event.risk_score)}           color={riskScoreColor(event.risk_score)} />
          <Field label="Network Load"      value={formatDecimal(event.network_load)}         color={loadColor(event.network_load ?? 0)} />
          <Field label="Anomaly Count"     value={event.anomaly_count_window} />
          <Field label="Max Consecutive"   value={event.max_consecutive_anomalies} />
          <Field label="Risk Level"        value={event.risk_level}                  color={riskColor[event.risk_level]} />
          <Field label="Action / Duration" value={actionLabel}                       color={riskColor[event.risk_level]} />
          <Field label="Time"              value={event.timestamp ? new Date(event.timestamp).toLocaleString() : '—'} />
        </div>

        {/* Footer */}
        <div style={{ borderTop: '1px solid var(--border)', paddingTop: 14, display: 'flex', justifyContent: 'flex-end', gap: 8, alignItems: 'center' }}>
          {blockError && <span style={{ fontSize: 10, color: 'var(--red)', marginRight: 'auto' }}>{blockError}</span>}

          <button onClick={onClose} style={{ padding: '7px 14px', borderRadius: 7, fontSize: 11, fontWeight: 600, background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border2)', color: 'var(--text2)', cursor: 'pointer', fontFamily: 'var(--font)' }}>
            Close
          </button>

          {isAlreadyBlocked ? (
            <button disabled style={{ padding: '7px 14px', borderRadius: 7, fontSize: 11, fontWeight: 600, background: 'rgba(239,68,68,0.05)', border: '1px solid rgba(239,68,68,0.2)', color: 'var(--red)', fontFamily: 'var(--font)', opacity: 0.55, cursor: 'not-allowed', display: 'flex', alignItems: 'center', gap: 6 }}>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M20 6L9 17l-5-5"/></svg>
              Already Blocked
            </button>
          ) : (
            <button onClick={handleBlock} disabled={blocking}
              style={{ padding: '7px 14px', borderRadius: 7, fontSize: 11, fontWeight: 600, background: 'var(--red-dim)', border: '1px solid rgba(239,68,68,0.3)', color: 'var(--red)', cursor: blocking ? 'wait' : 'pointer', fontFamily: 'var(--font)', display: 'flex', alignItems: 'center', gap: 6, transition: 'all 0.15s' }}
              onMouseOver={e => { if (!blocking) e.currentTarget.style.background = 'rgba(239,68,68,0.2)' }}
              onMouseOut={e => { e.currentTarget.style.background = 'var(--red-dim)' }}
            >
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
              {blocking ? 'Blocking...' : 'Block IP'}
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
