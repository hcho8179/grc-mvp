import { useState } from 'react'
import { useNavigate, Link, useSearchParams } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useTheme } from '../context/ThemeContext'
import { Icon } from '../components/Layout'

export default function Register() {
  const { register } = useAuth()
  const { t } = useTheme()
  const nav = useNavigate()
  const [params] = useSearchParams()
  const prefillSlug = params.get('invite') || ''

  const [form, setForm] = useState({ full_name: '', email: '', password: '', org_name: '', invite_slug: prefillSlug })
  const [joinMode, setJoinMode] = useState(!!prefillSlug)
  const [error, setError]       = useState('')
  const [loading, setLoading]   = useState(false)

  const set = (k) => (e) => setForm(f => ({ ...f, [k]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    if (form.password.length < 8) { setError('Password must be at least 8 characters'); return }
    if (!joinMode && !form.org_name.trim()) { setError('Organization name required'); return }
    setLoading(true)
    try {
      await register({ email: form.email, password: form.password, full_name: form.full_name,
                       org_name: joinMode ? '' : form.org_name, invite_slug: joinMode ? form.invite_slug : '' })
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
            <p className="font-bold text-base leading-none" style={{ color: t.text }}>Sentinel</p>
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
              { label: 'Password', key: 'password', type: 'password', placeholder: 'Min. 8 characters' },
            ].map(({ label, key, type, placeholder }) => (
              <div key={key}>
                <label className="block text-xs font-semibold mb-1.5" style={{ color: t.text2 }}>{label}</label>
                <input type={type} value={form[key]} onChange={set(key)} required
                       placeholder={placeholder} className={inputCls} style={inputStyle}
                       onFocus={e => e.target.style.boxShadow = `0 0 0 2px ${t.primary}40`}
                       onBlur={e => e.target.style.boxShadow = 'none'} />
              </div>
            ))}

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
                <label className="block text-xs font-semibold mb-1.5" style={{ color: t.text2 }}>Invite code</label>
                <input type="text" value={form.invite_slug} onChange={set('invite_slug')} required
                       placeholder="acme-security-inc" className={inputCls} style={inputStyle}
                       onFocus={e => e.target.style.boxShadow = `0 0 0 2px ${t.primary}40`}
                       onBlur={e => e.target.style.boxShadow = 'none'} />
                <p className="text-xs mt-1" style={{ color: t.text3 }}>Ask your workspace owner for the invite code</p>
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
