import { createContext, useContext, useState, useCallback } from 'react'

const ToastContext = createContext(null)

export function ToastProvider({ children }) {
  const [toast, setToast] = useState(null)

  const showToast = useCallback((msg, color = '#22d3ee') => {
    setToast({ msg, color })
    setTimeout(() => setToast(null), 3000)
  }, [])

  return (
    <ToastContext.Provider value={showToast}>
      {children}
      {toast && (
        <div style={{
          position: 'fixed', bottom: 24, right: 24,
          background: '#1e293b', border: '1px solid rgba(255,255,255,0.12)',
          borderRadius: 8, padding: '10px 16px', fontSize: 12,
          zIndex: 9999, display: 'flex', alignItems: 'center', gap: 8,
          animation: 'fadeIn 0.3s ease', color: toast.color,
          boxShadow: '0 8px 24px rgba(0,0,0,0.4)'
        }}>
          <span style={{ width: 8, height: 8, borderRadius: '50%', background: toast.color, flexShrink: 0 }} />
          {toast.msg}
        </div>
      )}
    </ToastContext.Provider>
  )
}

export const useToast = () => useContext(ToastContext)
