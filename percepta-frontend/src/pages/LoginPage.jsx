import { useState, useRef } from 'react'
import { useAuth } from '../hooks/useAuth'

export default function LoginPage() {
  const { login } = useAuth()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(false)
  const cardRef = useRef(null)

  function handleLogin() {
    const ok = login(username, password)
    if (!ok) {
      setError(true)
      setPassword('')
      if (cardRef.current) {
        cardRef.current.style.animation = 'none'
        void cardRef.current.offsetHeight
        cardRef.current.style.animation = 'shake 0.4s ease'
      }
    }
  }

  return (
    <div style={{
      position: 'fixed', inset: 0, background: 'var(--bg)',
      display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column',
      zIndex: 999,
    }}>
      {/* Grid bg */}
      <div style={{
        position: 'absolute', inset: 0,
        backgroundImage: 'linear-gradient(rgba(34,211,238,0.03) 1px,transparent 1px),linear-gradient(90deg,rgba(34,211,238,0.03) 1px,transparent 1px)',
        backgroundSize: '40px 40px', zIndex: 0,
      }} />
      <div style={{
        position: 'absolute', top: '20%', left: '50%', transform: 'translateX(-50%)',
        width: 600, height: 300,
        background: 'radial-gradient(ellipse,rgba(34,211,238,0.07) 0%,transparent 70%)',
        pointerEvents: 'none', zIndex: 0,
      }} />

      <div style={{ position: 'relative', zIndex: 1, width: 380 }}>
        {/* Logo */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 36, justifyContent: 'center' }}>
          <div style={{
            width: 42, height: 42,
            background: 'linear-gradient(135deg,#22d3ee,#0ea5e9)',
            borderRadius: 10, display: 'flex', alignItems: 'center', justifyContent: 'center',
            boxShadow: '0 0 24px rgba(34,211,238,0.3)',
          }}>
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
            </svg>
          </div>
          <div>
            <div style={{ fontSize: 20, fontWeight: 700, letterSpacing: 0.5 }}>Percepta</div>
            <div style={{ fontSize: 10, color: 'var(--text3)', letterSpacing: 1, textTransform: 'uppercase', marginTop: 2 }}>IDS/IPS System v2.0</div>
          </div>
        </div>

        {/* Card */}
        <div ref={cardRef} style={{
          background: 'var(--card)', border: '1px solid var(--border2)',
          borderRadius: 14, padding: '32px 28px', boxShadow: '0 20px 60px rgba(0,0,0,0.4)',
        }}>
          <div style={{ fontSize: 17, fontWeight: 700, marginBottom: 4 }}>Welcome back</div>
          <div style={{ fontSize: 11, color: 'var(--text3)', marginBottom: 28 }}>Sign in to access the security dashboard</div>

          {error && (
            <div style={{
              background: 'var(--red-dim)', border: '1px solid rgba(239,68,68,0.25)',
              borderRadius: 7, padding: '10px 14px', fontSize: 11, color: 'var(--red)',
              marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8,
            }}>
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
              </svg>
              Invalid username or password
            </div>
          )}

          {/* Username */}
          <div style={{ marginBottom: 16 }}>
            <label style={{ fontSize: 10, fontWeight: 600, letterSpacing: 1, textTransform: 'uppercase', color: 'var(--text3)', marginBottom: 7, display: 'block' }}>Username</label>
            <div style={{ position: 'relative' }}>
              <input
                value={username} onChange={e => { setUsername(e.target.value); setError(false) }}
                onKeyDown={e => e.key === 'Enter' && handleLogin()}
                type="text" placeholder="Enter your username" autoComplete="username"
                style={{
                  width: '100%', background: 'rgba(255,255,255,0.04)', border: '1px solid var(--border2)',
                  borderRadius: 8, padding: '11px 14px 11px 38px', color: 'var(--text)',
                  fontSize: 13, fontFamily: 'var(--font)', outline: 'none',
                }}
              />
              <span style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text3)', display: 'flex' }}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
              </span>
            </div>
          </div>

          {/* Password */}
          <div style={{ marginBottom: 16 }}>
            <label style={{ fontSize: 10, fontWeight: 600, letterSpacing: 1, textTransform: 'uppercase', color: 'var(--text3)', marginBottom: 7, display: 'block' }}>Password</label>
            <div style={{ position: 'relative' }}>
              <input
                value={password} onChange={e => { setPassword(e.target.value); setError(false) }}
                onKeyDown={e => e.key === 'Enter' && handleLogin()}
                type="password" placeholder="Enter your password" autoComplete="current-password"
                style={{
                  width: '100%', background: 'rgba(255,255,255,0.04)', border: '1px solid var(--border2)',
                  borderRadius: 8, padding: '11px 14px 11px 38px', color: 'var(--text)',
                  fontSize: 13, fontFamily: 'var(--font)', outline: 'none',
                }}
              />
              <span style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text3)', display: 'flex' }}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
              </span>
            </div>
          </div>

          <button onClick={handleLogin} style={{
            width: '100%', padding: 12,
            background: 'linear-gradient(135deg,#22d3ee,#0ea5e9)',
            border: 'none', borderRadius: 8, color: '#0d1117',
            fontSize: 13, fontWeight: 700, fontFamily: 'var(--font)',
            cursor: 'pointer', marginTop: 8, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
          }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/><polyline points="10 17 15 12 10 7"/><line x1="15" y1="12" x2="3" y2="12"/></svg>
            Sign In
          </button>
        </div>

        <div style={{ textAlign: 'center', marginTop: 20, fontSize: 10, color: 'var(--text3)' }}>
          Percepta · University Network Security
        </div>
      </div>
    </div>
  )
}
