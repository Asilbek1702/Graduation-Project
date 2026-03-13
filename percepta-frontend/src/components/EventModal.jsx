const riskColor = { LOW: 'var(--green)', MEDIUM: 'var(--yellow)', HIGH: 'var(--orange)', CRITICAL: 'var(--red)' }

function anomalyColor(v) { return v < 0.20 ? 'var(--red)' : v < 0.35 ? 'var(--orange)' : v < 0.50 ? 'var(--yellow)' : 'var(--green)' }
function stabColor(v)    { return v >= 0.75 ? 'var(--red)' : v >= 0.55 ? 'var(--orange)' : v >= 0.30 ? 'var(--yellow)' : 'var(--green)' }
function riskScoreColor(v){ return v >= 0.75 ? 'var(--red)' : v >= 0.50 ? 'var(--orange)' : v >= 0.30 ? 'var(--yellow)' : 'var(--green)' }
function loadColor(v)    { return v > 0.70 ? 'var(--orange)' : v > 0.30 ? 'var(--yellow)' : 'var(--green)' }

function Field({ label, value, color }) {
  return (
    <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border)', borderRadius: 7, padding: '10px 12px' }}>
      <div style={{ fontSize: 9, letterSpacing: 1, textTransform: 'uppercase', color: 'var(--text3)', marginBottom: 5 }}>{label}</div>
      <div style={{ fontSize: 13, fontWeight: 600, fontFamily: 'monospace', color: color || 'var(--text)' }}>{value ?? '—'}</div>
    </div>
  )
}

export default function EventModal({ event, onClose }) {
  if (!event) return null

  const actionLabel = event.action_duration_seconds > 0
    ? `${event.action_taken} · ${event.action_duration_seconds}s`
    : event.action_taken

  return (
    <div onClick={onClose} style={{
      position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.65)',
      backdropFilter: 'blur(3px)', zIndex: 200, display: 'flex', alignItems: 'center', justifyContent: 'center',
    }}>
      <div onClick={e => e.stopPropagation()} style={{
        background: '#161d2e', border: '1px solid rgba(34,211,238,0.2)',
        borderRadius: 12, width: 480, maxWidth: '95vw', padding: 22,
        animation: 'fadeIn 0.2s ease',
      }}>
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 18 }}>
          <div>
            <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--cyan)', fontFamily: 'monospace' }}>Event Details</div>
            <div style={{ fontSize: 10, color: 'var(--text3)', marginTop: 3, fontFamily: 'monospace' }}>{event.event_id}</div>
          </div>
          <button onClick={onClose} style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border)', borderRadius: 6, width: 26, height: 26, display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', color: 'var(--text2)', fontSize: 14 }}>✕</button>
        </div>

        {/* Fields grid */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 16 }}>
          <Field label="Source IP"        value={event.source_ip} />
          <Field label="Destination IP"   value={event.destination_ip} />
          <Field label="Anomaly Score"    value={event.anomaly_score?.toFixed(3)}   color={anomalyColor(event.anomaly_score)} />
          <Field label="Threshold"        value={event.adaptive_threshold?.toFixed(3)} />
          <Field label="Stability Score"  value={event.stability_score?.toFixed(3)} color={stabColor(event.stability_score ?? 0)} />
          <Field label="Risk Score"       value={event.risk_score?.toFixed(3)}      color={riskScoreColor(event.risk_score)} />
          <Field label="Network Load"     value={event.network_load?.toFixed(3)}    color={loadColor(event.network_load ?? 0)} />
          <Field label="Anomaly Count"    value={event.anomaly_count_window} />
          <Field label="Max Consecutive"  value={event.max_consecutive_anomalies} />
          <Field label="Risk Level"       value={event.risk_level}                  color={riskColor[event.risk_level]} />
          <Field label="Action / Duration" value={actionLabel}                      color={riskColor[event.risk_level]} />
          <Field label="Time"             value={event.timestamp ? new Date(event.timestamp).toLocaleString() : '—'} />
        </div>

        {/* Footer */}
        <div style={{ borderTop: '1px solid var(--border)', paddingTop: 14, display: 'flex', justifyContent: 'flex-end' }}>
          <button onClick={onClose} style={{ padding: '7px 14px', borderRadius: 7, fontSize: 11, fontWeight: 600, background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border2)', color: 'var(--text2)', cursor: 'pointer', fontFamily: 'var(--font)' }}>
            Close
          </button>
        </div>
      </div>
    </div>
  )
}
