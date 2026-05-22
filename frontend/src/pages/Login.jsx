import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useTheme } from '../context/ThemeContext'
import { Icon } from '../components/Layout'

export default function Login() {
  const { login } = useAuth()
  const { t } = useTheme()
  const nav = useNavigate()
  const [email, setEmail]       = useState('')
  const [password, setPassword] = useState('')
  const [error, setError]       = useState('')
  const [loading, setLoading]   = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(email, password)
      nav('/', { replace: true })
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4"
         style={{ background: t.bg }}>

      <div className="w-full max-w-sm">

        {/* Logo */}
        <div className="flex items-center gap-3 mb-8 justify-center">
          <div className="w-9 h-9 rounded-xl flex items-center justify-center"
               style={{ background: t.primary }}>
            <Icon name="shield" size={17} color="white" />
          </div>
          <div>
            <p className="font-bold text-base leading-none" style={{ color: t.text }}>Greenlight</p>
            <p className="text-xs mt-0.5" style={{ color: t.text3 }}>Close deals faster</p>
          </div>
        </div>

        {/* Card */}
        <div className="rounded-2xl p-7" style={t.card}>
          <h1 className="text-xl font-bold mb-0.5" style={{ color: t.text }}>Welcome back</h1>
          <p className="text-sm mb-6" style={{ color: t.text2 }}>Sign in to your workspace</p>

          {error && (
            <div className="mb-5 px-3.5 py-3 rounded-xl text-sm font-medium"
                 style={{ background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)', color: '#ef4444' }}>
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold mb-1.5" style={{ color: t.text2 }}>
                Email address
              </label>
              <input
                type="email" value={email} onChange={e => setEmail(e.target.value)}
                required placeholder="you@company.com"
                className="w-full px-3.5 py-2.5 rounded-xl text-sm outline-none transition-all"
                style={{ ...t.input }}
                onFocus={e => e.target.style.boxShadow = `0 0 0 2px ${t.primary}40`}
                onBlur={e => e.target.style.boxShadow = 'none'}
              />
            </div>
            <div>
              <label className="block text-xs font-semibold mb-1.5" style={{ color: t.text2 }}>
                Password
              </label>
              <input
                type="password" value={password} onChange={e => setPassword(e.target.value)}
                required placeholder="••••••••"
                className="w-full px-3.5 py-2.5 rounded-xl text-sm outline-none transition-all"
                style={{ ...t.input }}
                onFocus={e => e.target.style.boxShadow = `0 0 0 2px ${t.primary}40`}
                onBlur={e => e.target.style.boxShadow = 'none'}
              />
            </div>
            <div className="flex justify-end">
              <Link to="/forgot-password"
                    className="text-xs font-medium hover:underline"
                    style={{ color: t.text3 }}>
                Forgot password?
              </Link>
            </div>
            <button
              type="submit" disabled={loading}
              className="w-full py-2.5 rounded-xl text-sm font-semibold text-white transition-all
                         hover:opacity-90 disabled:opacity-55 mt-1"
              style={{ background: t.primary }}>
              {loading ? 'Signing in…' : 'Sign in'}
            </button>
          </form>
        </div>

        <p className="text-center text-sm mt-5" style={{ color: t.text3 }}>
          No account?{' '}
          <Link to="/register" className="font-semibold hover:underline" style={{ color: t.primary }}>
            Create workspace
          </Link>
        </p>
      </div>
    </div>
  )
}
