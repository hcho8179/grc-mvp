import { useState } from 'react'
import { useNavigate, useSearchParams, Link } from 'react-router-dom'
import { useTheme } from '../context/ThemeContext'
import { Icon } from '../components/Layout'

export default function ResetPassword() {
  const { t } = useTheme()
  const nav = useNavigate()
  const [params] = useSearchParams()
  const token = params.get('token') || ''

  const [password, setPassword]   = useState('')
  const [confirm, setConfirm]     = useState('')
  const [loading, setLoading]     = useState(false)
  const [error, setError]         = useState('')
  const [success, setSuccess]     = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (password !== confirm) { setError("Passwords don't match"); return }
    if (password.length < 8)  { setError("Password must be at least 8 characters"); return }
    setError('')
    setLoading(true)
    try {
      const res = await fetch('/api/auth/reset-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token, new_password: password }),
      })
      const data = await res.json()
      if (!res.ok) { setError(data.detail || 'Reset failed'); setLoading(false); return }
      setSuccess(true)
      setTimeout(() => nav('/login'), 2500)
    } catch {
      setError('Something went wrong. Please try again.')
    }
    setLoading(false)
  }

  if (!token) return (
    <div className="min-h-screen flex items-center justify-center" style={{ background: t.bg }}>
      <div className="text-center">
        <p className="text-sm font-medium mb-4" style={{ color: t.text2 }}>Invalid reset link.</p>
        <Link to="/forgot-password" className="font-semibold hover:underline text-sm"
              style={{ color: t.primary }}>Request a new one</Link>
      </div>
    </div>
  )

  return (
    <div className="min-h-screen flex items-center justify-center px-4"
         style={{ background: t.bg }}>
      <div className="w-full max-w-sm">

        <div className="flex items-center gap-3 mb-8 justify-center">
          <div className="w-9 h-9 rounded-xl flex items-center justify-center"
               style={{ background: t.primary }}>
            <Icon name="shield" size={17} color="white" />
          </div>
          <div>
            <p className="font-bold text-base leading-none" style={{ color: t.text }}>Sentinel</p>
            <p className="text-xs mt-0.5" style={{ color: t.text3 }}>GRC Automation</p>
          </div>
        </div>

        <div className="rounded-2xl p-7" style={t.card}>
          {!success ? (
            <>
              <h1 className="text-xl font-bold mb-1" style={{ color: t.text }}>Set new password</h1>
              <p className="text-sm mb-6" style={{ color: t.text2 }}>
                Choose a strong password — minimum 8 characters.
              </p>

              {error && (
                <div className="mb-4 px-3.5 py-3 rounded-xl text-sm font-medium"
                     style={{ background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)', color: '#ef4444' }}>
                  {error}
                </div>
              )}

              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold mb-1.5" style={{ color: t.text2 }}>
                    New password
                  </label>
                  <input type="password" value={password} onChange={e => setPassword(e.target.value)}
                         required placeholder="Min. 8 characters"
                         className="w-full px-3.5 py-2.5 rounded-xl text-sm outline-none transition-all"
                         style={{ ...t.input }}
                         onFocus={e => e.target.style.boxShadow = `0 0 0 2px ${t.primary}40`}
                         onBlur={e => e.target.style.boxShadow = 'none'} />
                </div>
                <div>
                  <label className="block text-xs font-semibold mb-1.5" style={{ color: t.text2 }}>
                    Confirm new password
                  </label>
                  <input type="password" value={confirm} onChange={e => setConfirm(e.target.value)}
                         required placeholder="Repeat password"
                         className="w-full px-3.5 py-2.5 rounded-xl text-sm outline-none transition-all"
                         style={{ ...t.input }}
                         onFocus={e => e.target.style.boxShadow = `0 0 0 2px ${t.primary}40`}
                         onBlur={e => e.target.style.boxShadow = 'none'} />
                </div>
                <button type="submit" disabled={loading}
                        className="w-full py-2.5 rounded-xl text-sm font-semibold text-white
                                   hover:opacity-90 disabled:opacity-55 transition-all"
                        style={{ background: t.primary }}>
                  {loading ? 'Saving…' : 'Set new password'}
                </button>
              </form>
            </>
          ) : (
            <div className="text-center py-4">
              <div className="w-12 h-12 rounded-xl mx-auto mb-4 flex items-center justify-center"
                   style={{ background: 'rgba(34,197,94,0.1)', border: '1px solid rgba(34,197,94,0.2)' }}>
                <Icon name="check" size={22} color="#16a34a" />
              </div>
              <h2 className="text-lg font-bold mb-2" style={{ color: t.text }}>Password updated</h2>
              <p className="text-sm" style={{ color: t.text2 }}>Redirecting to sign in…</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
