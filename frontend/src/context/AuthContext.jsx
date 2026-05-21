import { createContext, useContext, useState, useEffect } from 'react'

const AuthContext = createContext(null)

const USER_KEY = 'sentinel_user'   // only non-sensitive user info, no token

export function AuthProvider({ children }) {
  const [user,    setUser]    = useState(() => {
    try { return JSON.parse(localStorage.getItem(USER_KEY)) } catch { return null }
  })
  const [loading, setLoading] = useState(true)

  // On mount, verify the cookie is still valid with the server
  useEffect(() => {
    fetch('/api/auth/me', { credentials: 'include' })
      .then(r => r.ok ? r.json() : Promise.reject())
      .then(u => { setUser(u); localStorage.setItem(USER_KEY, JSON.stringify(u)) })
      .catch(() => { setUser(null); localStorage.removeItem(USER_KEY) })
      .finally(() => setLoading(false))
  }, [])

  const saveUser = (u) => {
    setUser(u)
    localStorage.setItem(USER_KEY, JSON.stringify(u))
  }

  const logout = async () => {
    await fetch('/api/auth/logout', { method: 'POST', credentials: 'include' })
    setUser(null)
    localStorage.removeItem(USER_KEY)
  }

  const _parseJson = async (res, fallback) => {
    try { return await res.json() } catch { return { detail: fallback } }
  }

  const login = async (email, password) => {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    })
    const data = await _parseJson(res, 'Login failed')
    if (!res.ok) throw new Error(data.detail || 'Login failed')
    saveUser(data.user)
    return data.user
  }

  const register = async (payload) => {
    const res = await fetch('/api/auth/register', {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    const data = await _parseJson(res, 'Registration failed')
    if (!res.ok) throw new Error(data.detail || 'Registration failed')
    saveUser(data.user)
    return data.user
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, register }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
