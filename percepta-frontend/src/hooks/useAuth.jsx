import { createContext, useContext, useState } from 'react'

const AuthContext = createContext(null)

const USERS = [
  { username: 'admin',    password: 'admin123',      role: 'Security Ops',     name: 'Admin User' },
  { username: 'security', password: 'sentinel2024',  role: 'Security Analyst', name: 'Security Team' },
]

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const saved = sessionStorage.getItem('percepta_user')
    return saved ? JSON.parse(saved) : null
  })

  function login(username, password) {
    const found = USERS.find(u => u.username === username && u.password === password)
    if (!found) return false
    sessionStorage.setItem('percepta_user', JSON.stringify(found))
    setUser(found)
    return true
  }

  function logout() {
    sessionStorage.removeItem('percepta_user')
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
