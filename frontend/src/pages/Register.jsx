import { useState } from 'react'
import { useNavigate, Link, useSearchParams } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useTheme } from '../context/ThemeContext'
import { Icon } from '../components/Layout'

function PasswordStrength({ password }) {
  const checks = [
    { label: '8+ chars',    ok: password.length >= 8 },
    { label: 'Uppercase',   ok: /[A-Z]/.test(password) },
    { label: 'Number',      ok: /[0-9]/.test(password) },
    { label: 'Symbol',      ok: /[^A-Za-z0-9]/.test(password) },
  ]
  if (!password) return null
  return (
    <div className="flex gap-3 mt-1.5 flex-wrap">
      {checks.map(({ label, ok }) => (
        <span key={label} className="flex items-center gap-1 text-[10px]"
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

  const [form, setForm] = useState({
    full_name: '',
    email: '',
    password: '',
    workspace_name: '',
    invite_token: prefillToken,
  })
  const [joinMode, setJoinMode] = useState(!!prefillToken)
  const [workspaceType, setWorkspaceType] = useState('consultant')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const set = (k) => (e) => setForm(f => ({ ...f, [k]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    if (!passwordValid(form.password)) { setError('Password does not meet the requirements below'); return }
    if (!joinMode && !form.workspace_name.trim()) { setError('Company name required'); return }
    setLoading(true)
    try {
      await register({
        email: form.email,
        password: form.password,
        full_name: form.full_name,
        workspace_name: joinMode ? '' : form.workspace_name,
        invite_token: joinMode ? form.invite_token : '',
        workspace_type: joinMode ? 'consultant' : workspaceType,
      })
      nav('/', { replace: true })
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const inputCls = 'w-full px-3 py-2 rounded-lg text-sm outline-none transition-all'

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-4"
         style={{ background: t.bg }}>
      <div className="w-full max-w-sm">

        {/* Logo */}
        <div className="flex items-center gap-2.5 mb-4 justify-center">
          <div className="w-8 h-8 rounded-lg flex items-center justify-center"
               style={{ background: t.primary }}>
            <Icon name="shield" size={15} color="white" />
          </div>
          <div>
            <p className="font-bold text-sm leading-none" style={{ color: t.text }}>Greenlight</p>
            <p className="text-[10px] mt-0.5" style={{ color: t.text3 }}>Close deals faster</p>
          </div>
        </div>

        <div className="rounded-2xl p-5" style={t.card}>
          <div className="flex items-baseline justify-between mb-3">
            <h1 className="text-lg font-bold" style={{ color: t.text }}>Create account</h1>
            <p className="text-xs" style={{ color: t.text3 }}>
              {joinMode ? 'Join your team' : 'Free workspace'}
            </p>
          </div>

          {/* Tab switcher */}
          <div className="flex gap-1 mb-3 p-0.5 rounded-lg"
               style={{ background: t.dark ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.04)' }}>
            {[['New workspace', false], ['Join with invite', true]].map(([label, mode]) => (
              <button key={label} type="button" onClick={() => setJoinMode(mode)}
                      className="flex-1 py-1.5 rounded-md text-xs font-semibold transition-all"
                      style={joinMode === mode
                        ? { background: t.primary, color: 'white' }
                        : { color: t.text3 }}>
                {label}
              </button>
            ))}
          </div>

          {error && (
            <div className="mb-3 px-3 py-2.5 rounded-lg text-xs font-medium"
                 style={{ background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)', color: '#ef4444' }}>
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-2.5">
            {[
              { label: 'Full name', key: 'full_name', type: 'text',  placeholder: 'Jane Smith' },
              { label: 'Email',     key: 'email',     type: 'email', placeholder: 'you@company.com' },
            ].map(({ label, key, type, placeholder }) => (
              <div key={key}>
                <label className="block text-xs font-semibold mb-1" style={{ color: t.text2 }}>{label}</label>
                <input type={type} value={form[key]} onChange={set(key)} required
                       placeholder={placeholder} className={inputCls} style={{ ...t.input }}
                       onFocus={e => e.target.style.boxShadow = `0 0 0 2px ${t.primary}40`}
                       onBlur={e => e.target.style.boxShadow = 'none'} />
              </div>
            ))}

            <div>
              <label className="block text-xs font-semibold mb-1" style={{ color: t.text2 }}>Password</label>
              <input type="password" value={form.password} onChange={set('password')} required
                     placeholder="Min. 8 characters" className={inputCls} style={{ ...t.input }}
                     onFocus={e => e.target.style.boxShadow = `0 0 0 2px ${t.primary}40`}
                     onBlur={e => e.target.style.boxShadow = 'none'} />
              <PasswordStrength password={form.password} />
            </div>

            {!joinMode ? (
              <>
                <div>
                  <label className="block text-xs font-semibold mb-1" style={{ color: t.text2 }}>Company name</label>
                  <input type="text" value={form.workspace_name} onChange={set('workspace_name')} required
                         placeholder="Acme Security Inc." className={inputCls} style={{ ...t.input }}
                         onFocus={e => e.target.style.boxShadow = `0 0 0 2px ${t.primary}40`}
                         onBlur={e => e.target.style.boxShadow = 'none'} />
                </div>
                <div>
                  <label className="block text-xs font-semibold mb-1.5" style={{ color: t.text2 }}>How do you use Greenlight?</label>
                  <div className="grid grid-cols-2 gap-2">
                    {[
                      { type: 'consultant', title: 'Consulting firm', sub: 'Managing multiple clients' },
                      { type: 'company',    title: 'Company',         sub: 'Our own security team' },
                    ].map(({ type, title, sub }) => {
                      const active = workspaceType === type
                      return (
                        <button key={type} type="button" onClick={() => setWorkspaceType(type)}
                                className="flex flex-col items-start px-3 py-2.5 rounded-lg text-left transition-all"
                                style={{
                                  border: `1.5px solid ${active ? t.primary : (t.dark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)')}`,
                                  background: active ? `${t.primary}14` : 'transparent',
                                }}>
                          <span className="text-xs font-semibold" style={{ color: active ? t.primary : t.text }}>{title}</span>
                          <span className="text-[10px] mt-0.5" style={{ color: t.text3 }}>{sub}</span>
                        </button>
                      )
                    })}
                  </div>
                </div>
              </>
            ) : (
              <div>
                <label className="block text-xs font-semibold mb-1" style={{ color: t.text2 }}>Invite link</label>
                {form.invite_token ? (
                  <div className="flex items-center gap-2 px-3 py-2 rounded-lg text-xs"
                       style={{ ...t.input, color: '#16a34a', border: '1px solid rgba(34,197,94,0.3)' }}>
                    ✓ Invite link detected
                  </div>
                ) : (
                  <p className="text-xs px-1" style={{ color: '#ef4444' }}>
                    No invite link found. Ask your workspace admin for a new link.
                  </p>
                )}
              </div>
            )}

            <button type="submit" disabled={loading}
                    className="w-full py-2 rounded-lg text-sm font-semibold text-white transition-all hover:opacity-90 disabled:opacity-55"
                    style={{ background: t.primary }}>
              {loading ? 'Creating account…' : joinMode ? 'Join workspace' : 'Create workspace'}
            </button>
          </form>
        </div>

        <p className="text-center text-xs mt-3" style={{ color: t.text3 }}>
          Already have an account?{' '}
          <Link to="/login" className="font-semibold hover:underline" style={{ color: t.primary }}>Sign in</Link>
        </p>
      </div>
    </div>
  )
}
