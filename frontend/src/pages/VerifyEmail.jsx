import { useState, useEffect } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import { api } from '../api'
import { useTheme } from '../context/ThemeContext'
import { Icon } from '../components/Layout'

export default function VerifyEmail() {
  const { t } = useTheme()
  const [params] = useSearchParams()
  const token = params.get('token') || ''

  const [status, setStatus] = useState('verifying') // verifying | success | error
  const [errorMsg, setErrorMsg] = useState('')

  useEffect(() => {
    if (!token) { setStatus('error'); setErrorMsg('No verification token found.'); return }
    api.verifyEmail(token)
      .then(() => setStatus('success'))
      .catch(err => { setStatus('error'); setErrorMsg(err.message || 'Verification failed.') })
  }, [token])

  return (
    <div className="min-h-screen flex items-center justify-center px-4"
         style={{ background: t.bg }}>
      <div className="w-full max-w-sm text-center">

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

        <div className="rounded-2xl p-8" style={t.card}>
          {status === 'verifying' && (
            <>
              <div className="w-12 h-12 rounded-full mx-auto mb-4 flex items-center justify-center"
                   style={{ background: 'rgba(59,130,246,0.1)' }}>
                <span className="spin inline-block text-2xl" style={{ color: t.primary }}>↻</span>
              </div>
              <p className="font-semibold" style={{ color: t.text }}>Verifying your email…</p>
            </>
          )}

          {status === 'success' && (
            <>
              <div className="w-12 h-12 rounded-full mx-auto mb-4 flex items-center justify-center"
                   style={{ background: 'rgba(22,163,74,0.1)', border: '1px solid rgba(22,163,74,0.25)' }}>
                <Icon name="check" size={22} color="#16a34a" />
              </div>
              <p className="font-bold text-lg mb-1" style={{ color: t.text }}>Email verified!</p>
              <p className="text-sm mb-5" style={{ color: t.text2 }}>Your account is now fully verified.</p>
              <Link to="/"
                    className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold text-white hover:opacity-90 no-underline"
                    style={{ background: t.primary }}>
                Go to dashboard
              </Link>
            </>
          )}

          {status === 'error' && (
            <>
              <div className="w-12 h-12 rounded-full mx-auto mb-4 flex items-center justify-center"
                   style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.25)' }}>
                <span className="text-2xl">✕</span>
              </div>
              <p className="font-bold text-lg mb-1" style={{ color: t.text }}>Verification failed</p>
              <p className="text-sm mb-5" style={{ color: '#ef4444' }}>{errorMsg}</p>
              <Link to="/"
                    className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold text-white hover:opacity-90 no-underline"
                    style={{ background: t.primary }}>
                Back to app
              </Link>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
