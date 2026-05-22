import { useState } from 'react'
import { useNavigate, Link, useSearchParams } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useTheme } from '../context/ThemeContext'
import { Icon } from '../components/Layout'

function PasswordStrength({ password }) {
  const checks = [
    { label: '8+ characters',    ok: password.length >= 8 },
    { label: 'Uppercase letter', ok: /[A-Z]/.test(password) },
    { label: 'Number',           ok: /[0-9]/.test(password) },
    { label: 'Symbol (!@#$…)',   ok: /[^A-Za-z0-9]/.test(password) },
  ]
  if (!password) return null
  return (
    <div className="flex flex-wrap gap-x-4 gap-y-1 mt-2">
      {checks.map(({ label, ok }) => (
        <span key={label} className="flex items-center gap-1 text-xs"
              style={{ color: ok ? '#16a34a' : '#94a3b8' }}>
          <span className="font-bold">{ok ? '✓' : '○'}</span> {label}
        </span>
      ))}
    </div>
  )
}

function passwordValid(p) {
  return p.length >= 8 && /[A-Z]/.test(p) && /[0-9]/.test(p) && /[^A-Za-z0-9]/.test(p)
}

export default function Register() {
  const { register } = useAuth()
  const { t } = useTheme()
  const nav = useNavigate()
  const [params] = useSearchParams()
  const prefillToken = params.get('token') || ''

  const [form, setForm] = useState({ full_name: '', email: '', password: '', org_name: '', invite_token: prefillToken })
  const [joinMode, setJoinMode] = useState(!!prefillToken)
  const [error, setError]       = useState('')
  const [loading, setLoading]   = useState(false)

  const set = (k) => (e) => setForm(f => ({ ...f, [k]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    if (!passwordValid(form.password)) { setError('Password does not meet the requirements below'); return }
    if (!joinMode && !form.org_name.trim()) { setError('Organization name required'); return }
    setLoading(true)
    try {
      await register({ email: form.email, password: form.password, full_name: form.full_name,
                       org_name: joinMode ? '' : form.org_name, invite_token: joinMode ? form.invite_token : '' })
      nav('/', { replace: true })
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const inputStyle = { ...t.input }
  const inputCls = 'w-full px-3.5 py-2.5 rounded-xl text-sm outline-none transition-all'

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-10"
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
            <p className="text-xs mt-0.5" style={{ color: t.text3 }}>GRC Automation</p>
          </div>
        </div>

        <div className="rounded-2xl p-7" style={t.card}>
          <h1 className="text-xl font-bold mb-0.5" style={{ color: t.text }}>Create account</h1>
          <p className="text-sm mb-5" style={{ color: t.text2 }}>Start your free workspace</p>

          {/* Tab switcher */}
          <div className="flex gap-1 mb-5 p-1 rounded-xl"
               style={{ background: t.dark ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.04)' }}>
            {[['New workspace', false], ['Join with invite', true]].map(([label, mode]) => (
              <button key={label} type="button" onClick={() => setJoinMode(mode)}
                      className="flex-1 py-1.5 rounded-lg text-xs font-semibold transition-all"
                      style={joinMode === mode
                        ? { background: t.primary, color: 'white' }
                        : { color: t.text3 }}>
                {label}
              </button>
            ))}
          </div>

          {error && (
            <div className="mb-4 px-3.5 py-3 rounded-xl text-sm font-medium"
                 style={{ background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)', color: '#ef4444' }}>
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-3.5">
            {[
              { label: 'Full name', key: 'full_name', type: 'text', placeholder: 'Jane Smith' },
              { label: 'Email', key: 'email', type: 'email', placeholder: 'you@company.com' },
            ].map(({ label, key, type, placeholder }) => (
              <div key={key}>
                <label className="block text-xs font-semibold mb-1.5" style={{ color: t.text2 }}>{label}</label>
                <input type={type} value={form[key]} onChange={set(key)} required
                       placeholder={placeholder} className={inputCls} style={inputStyle}
                       onFocus={e => e.target.style.boxShadow = `0 0 0 2px ${t.primary}40`}
                       onBlur={e => e.target.style.boxShadow = 'none'} />
              </div>
            ))}
            <div>
              <label className="block text-xs font-semibold mb-1.5" style={{ color: t.text2 }}>Password</label>
              <input type="password" value={form.password} onChange={set('password')} required
                     placeholder="Min. 8 characters" className={inputCls} style={inputStyle}
                     onFocus={e => e.target.style.boxShadow = `0 0 0 2px ${t.primary}40`}
                     onBlur={e => e.target.style.boxShadow = 'none'} />
              <PasswordStrength password={form.password} />
            </div>

            {!joinMode ? (
              <div>
                <label className="block text-xs font-semibold mb-1.5" style={{ color: t.text2 }}>Organization name</label>
                <input type="text" value={form.org_name} onChange={set('org_name')} required
                       placeholder="Acme Security Inc." className={inputCls} style={inputStyle}
                       onFocus={e => e.target.style.boxShadow = `0 0 0 2px ${t.primary}40`}
                       onBlur={e => e.target.style.boxShadow = 'none'} />
              </div>
            ) : (
              <div>
                <label className="block text-xs font-semibold mb-1.5" style={{ color: t.text2 }}>Invite link</label>
                {form.invite_token ? (
                  <div className="flex items-center gap-2 px-3.5 py-2.5 rounded-xl text-sm"
                       style={{ ...t.input, color: '#16a34a', border: '1px solid rgba(34,197,94,0.3)' }}>
                    ✓ Invite link detected
                  </div>
                ) : (
                  <p className="text-xs px-1" style={{ color: '#ef4444' }}>
                    No invite link found. Ask your workspace admin to send you a new invite link.
                  </p>
                )}
              </div>
            )}

            <button type="submit" disabled={loading}
                    className="w-full py-2.5 rounded-xl text-sm font-semibold text-white transition-all hover:opacity-90 disabled:opacity-55 mt-1"
                    style={{ background: t.primary }}>
              {loading ? 'Creating account…' : joinMode ? 'Join workspace' : 'Create workspace'}
            </button>
          </form>
        </div>

        {!joinMode && (
          <div className="mt-4 rounded-xl px-4 py-3.5"
               style={{ background: t.dark ? 'rgba(59,130,246,0.06)' : 'rgba(59,130,246,0.05)',
                        border: `1px solid ${t.dark ? 'rgba(59,130,246,0.15)' : 'rgba(59,130,246,0.15)'}` }}>
            <p className="text-xs font-semibold mb-2" style={{ color: t.text2 }}>What's included:</p>
            <div className="space-y-1.5">
              {[
                '20 SOC 2 / ISO 27001 policy templates — start immediately, no setup needed',
                'Upload your own policies for accurate, company-specific answers',
                'Every answer reviewed and approved by your team before use',
              ].map(item => (
                <div key={item} className="flex items-start gap-2 text-xs" style={{ color: t.text2 }}>
                  <span className="font-bold flex-shrink-0 mt-px" style={{ color: t.primary }}>✓</span>
                  {item}
                </div>
              ))}
            </div>
          </div>
        )}

        <p className="text-center text-sm mt-5" style={{ color: t.text3 }}>
          Already have an account?{' '}
          <Link to="/login" className="font-semibold hover:underline" style={{ color: t.primary }}>Sign in</Link>
        </p>
      </div>
    </div>
  )
}
