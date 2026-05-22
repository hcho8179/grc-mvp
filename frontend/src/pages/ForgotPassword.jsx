import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useTheme } from '../context/ThemeContext'
import { Icon } from '../components/Layout'

export default function ForgotPassword() {
  const { t } = useTheme()
  const [email, setEmail]       = useState('')
  const [submitted, setSubmitted] = useState(false)
  const [loading, setLoading]   = useState(false)
  const [error, setError]       = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await fetch('/api/auth/forgot-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      })
      setSubmitted(true)
    } catch {
      setError('Something went wrong. Please try again.')
    }
    setLoading(false)
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

        <div className="rounded-2xl p-7" style={t.card}>
          {!submitted ? (
            <>
              <h1 className="text-xl font-bold mb-1" style={{ color: t.text }}>Forgot password?</h1>
              <p className="text-sm mb-6" style={{ color: t.text2 }}>
                Enter your email and we'll send you a reset link.
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
                <button type="submit" disabled={loading}
                        className="w-full py-2.5 rounded-xl text-sm font-semibold text-white
                                   hover:opacity-90 disabled:opacity-55 transition-all"
                        style={{ background: t.primary }}>
                  {loading ? 'Sending…' : 'Send reset link'}
                </button>
              </form>
            </>
          ) : (
            <div className="text-center py-4">
              <div className="w-12 h-12 rounded-xl mx-auto mb-4 flex items-center justify-center"
                   style={{ background: 'rgba(34,197,94,0.1)', border: '1px solid rgba(34,197,94,0.2)' }}>
                <Icon name="check" size={22} color="#16a34a" />
              </div>
              <h2 className="text-lg font-bold mb-2" style={{ color: t.text }}>Check your email</h2>
              <p className="text-sm" style={{ color: t.text2 }}>
                If <strong>{email}</strong> has an account, a reset link is on its way.
                It expires in 15 minutes.
              </p>
            </div>
          )}
        </div>

        <p className="text-center text-sm mt-5" style={{ color: t.text3 }}>
          <Link to="/login" className="font-semibold hover:underline" style={{ color: t.primary }}>
            Back to sign in
          </Link>
        </p>
      </div>
    </div>
  )
}
