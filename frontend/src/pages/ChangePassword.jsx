import { useState } from 'react'
import { useTheme } from '../context/ThemeContext'
import { Icon } from '../components/Layout'

export default function ChangePassword() {
  const { t } = useTheme()
  const [form, setForm] = useState({ current: '', next: '', confirm: '' })
  const [loading, setLoading] = useState(false)
  const [error, setError]   = useState('')
  const [success, setSuccess] = useState(false)

  const set = k => e => setForm(f => ({ ...f, [k]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (form.next !== form.confirm) { setError("New passwords don't match"); return }
    if (form.next.length < 8)       { setError("Password must be at least 8 characters"); return }
    setError('')
    setLoading(true)
    try {
      const res = await fetch('/api/auth/change-password', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ current_password: form.current, new_password: form.next }),
      })
      const data = await res.json()
      if (!res.ok) { setError(data.detail || 'Failed to change password'); setLoading(false); return }
      setSuccess(true)
      setForm({ current: '', next: '', confirm: '' })
    } catch {
      setError('Something went wrong. Please try again.')
    }
    setLoading(false)
  }

  const inputCls = 'w-full px-3.5 py-2.5 rounded-xl text-sm outline-none transition-all'

  return (
    <div className="h-full overflow-y-auto">
      <div className="p-8 max-w-md mx-auto">

        <div className="mb-8">
          <h1 className="text-2xl font-bold" style={{ color: t.text }}>Change Password</h1>
          <p className="text-sm mt-0.5" style={{ color: t.text2 }}>
            Update your account password
          </p>
        </div>

        <div className="rounded-2xl p-6" style={t.card}>
          {success ? (
            <div className="text-center py-6">
              <div className="w-12 h-12 rounded-xl mx-auto mb-4 flex items-center justify-center"
                   style={{ background: 'rgba(34,197,94,0.1)', border: '1px solid rgba(34,197,94,0.2)' }}>
                <Icon name="check" size={22} color="#16a34a" />
              </div>
              <h2 className="text-base font-bold mb-1" style={{ color: t.text }}>Password updated</h2>
              <p className="text-sm" style={{ color: t.text2 }}>Your new password is active.</p>
              <button onClick={() => setSuccess(false)}
                      className="mt-4 text-sm font-semibold hover:underline"
                      style={{ color: t.primary }}>
                Change again
              </button>
            </div>
          ) : (
            <>
              {error && (
                <div className="mb-5 px-3.5 py-3 rounded-xl text-sm font-medium"
                     style={{ background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)', color: '#ef4444' }}>
                  {error}
                </div>
              )}

              <form onSubmit={handleSubmit} className="space-y-4">
                {[
                  { label: 'Current password', key: 'current', placeholder: '••••••••' },
                  { label: 'New password',     key: 'next',    placeholder: 'Min. 8 characters' },
                  { label: 'Confirm new password', key: 'confirm', placeholder: 'Repeat new password' },
                ].map(({ label, key, placeholder }) => (
                  <div key={key}>
                    <label className="block text-xs font-semibold mb-1.5" style={{ color: t.text2 }}>
                      {label}
                    </label>
                    <input type="password" value={form[key]} onChange={set(key)}
                           required placeholder={placeholder}
                           className={inputCls} style={{ ...t.input }}
                           onFocus={e => e.target.style.boxShadow = `0 0 0 2px ${t.primary}40`}
                           onBlur={e => e.target.style.boxShadow = 'none'} />
                  </div>
                ))}

                <button type="submit" disabled={loading}
                        className="w-full py-2.5 rounded-xl text-sm font-semibold text-white
                                   hover:opacity-90 disabled:opacity-55 transition-all mt-1"
                        style={{ background: t.primary }}>
                  {loading ? 'Saving…' : 'Update password'}
                </button>
              </form>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
