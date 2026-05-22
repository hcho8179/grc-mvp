import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api } from '../api'
import { useTheme } from '../context/ThemeContext'
import { Icon } from '../components/Layout'

export default function InvitePage() {
  const { token } = useParams()
  const { t } = useTheme()
  const nav = useNavigate()
  const [status, setStatus] = useState('loading') // loading | valid | invalid
  const [orgName, setOrgName] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    api.validateInvite(token)
      .then(d => { setOrgName(d.org_name); setStatus('valid') })
      .catch(e => { setError(e.message); setStatus('invalid') })
  }, [token])

  if (status === 'loading') return (
    <div className="min-h-screen flex items-center justify-center" style={{ background: t.bg }}>
      <div className="skeleton w-64 h-32 rounded-2xl" />
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
            <p className="font-bold text-base leading-none" style={{ color: t.text }}>Greenlight</p>
            <p className="text-xs mt-0.5" style={{ color: t.text3 }}>Close deals faster</p>
          </div>
        </div>

        <div className="rounded-2xl p-7 text-center" style={t.card}>
          {status === 'valid' ? (
            <>
              <div className="w-12 h-12 rounded-xl mx-auto mb-4 flex items-center justify-center"
                   style={{ background: 'rgba(59,130,246,0.1)', border: '1px solid rgba(59,130,246,0.2)' }}>
                <Icon name="user" size={22} color={t.primary} />
              </div>
              <h1 className="text-xl font-bold mb-1" style={{ color: t.text }}>You're invited</h1>
              <p className="text-sm mb-6" style={{ color: t.text2 }}>
                Join <strong>{orgName}</strong> on Greenlight
              </p>
              <button
                onClick={() => nav(`/register?token=${token}`)}
                className="w-full py-2.5 rounded-xl text-sm font-semibold text-white hover:opacity-90 transition-all"
                style={{ background: t.primary }}>
                Accept invite & create account
              </button>
              <p className="text-xs mt-4" style={{ color: t.text3 }}>
                Already have an account?{' '}
                <button className="font-semibold hover:underline" style={{ color: t.primary }}
                        onClick={() => nav('/login')}>
                  Sign in
                </button>
              </p>
            </>
          ) : (
            <>
              <div className="w-12 h-12 rounded-xl mx-auto mb-4 flex items-center justify-center"
                   style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.2)' }}>
                <Icon name="x" size={22} color="#ef4444" />
              </div>
              <h1 className="text-xl font-bold mb-2" style={{ color: t.text }}>Invite invalid</h1>
              <p className="text-sm" style={{ color: t.text2 }}>{error}</p>
              <p className="text-xs mt-4" style={{ color: t.text3 }}>
                Ask your workspace admin to send a new invite link.
              </p>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
