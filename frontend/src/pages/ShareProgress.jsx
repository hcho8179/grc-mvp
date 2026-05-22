import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { api } from '../api'

export default function ShareProgress() {
  const { token } = useParams()
  const [data, setData] = useState(null)
  const [error, setError] = useState(false)
  const [lastUpdated, setLastUpdated] = useState(null)

  const load = () => {
    api.getShareProgress(token)
      .then(d => {
        if (d.error) { setError(true); return }
        setData(d)
        setLastUpdated(new Date())
      })
      .catch(() => setError(true))
  }

  useEffect(() => {
    load()
    const iv = setInterval(load, 30000)
    return () => clearInterval(iv)
  }, [token])

  if (error) return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#f8fafc' }}>
      <div style={{ textAlign: 'center', padding: '40px' }}>
        <p style={{ fontSize: 48, marginBottom: 12 }}>🔒</p>
        <p style={{ fontSize: 18, fontWeight: 700, color: '#0f172a', marginBottom: 6 }}>Link not found</p>
        <p style={{ fontSize: 14, color: '#64748b' }}>This progress link is invalid or has been removed.</p>
      </div>
    </div>
  )

  if (!data) return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#f8fafc' }}>
      <div style={{ width: 40, height: 40, borderRadius: '50%', border: '3px solid #e2e8f0', borderTopColor: '#2563eb', animation: 'spin 0.8s linear infinite' }} />
    </div>
  )

  const pct = data.pct
  const barColor = pct === 100 ? '#16a34a' : '#2563eb'

  return (
    <div style={{ minHeight: '100vh', background: '#f8fafc', fontFamily: 'system-ui, sans-serif' }}>
      <div style={{ maxWidth: 520, margin: '0 auto', padding: '60px 24px' }}>

        {/* Brand */}
        <div style={{ marginBottom: 32 }}>
          <span style={{ background: '#2563eb', color: 'white', padding: '5px 12px', borderRadius: 8, fontSize: 13, fontWeight: 700 }}>
            Greenlight
          </span>
        </div>

        {/* Header */}
        <div style={{ marginBottom: 32 }}>
          {data.customer_name && (
            <p style={{ fontSize: 13, color: '#64748b', marginBottom: 4, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              {data.customer_name}
            </p>
          )}
          <h1 style={{ fontSize: 22, fontWeight: 700, color: '#0f172a', margin: 0, lineHeight: 1.3 }}>
            {data.name}
          </h1>
        </div>

        {/* Progress card */}
        <div style={{ background: 'white', borderRadius: 16, padding: 28, boxShadow: '0 1px 3px rgba(0,0,0,0.08)', border: '1px solid #e2e8f0', marginBottom: 20 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
            <p style={{ fontSize: 13, fontWeight: 600, color: '#475569', margin: 0 }}>Review progress</p>
            <p style={{ fontSize: 22, fontWeight: 700, color: barColor, margin: 0 }}>{pct}%</p>
          </div>
          <div style={{ height: 8, borderRadius: 8, background: '#f1f5f9', overflow: 'hidden', marginBottom: 20 }}>
            <div style={{ height: '100%', width: `${pct}%`, background: barColor, borderRadius: 8, transition: 'width 0.5s ease' }} />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12 }}>
            {[
              { label: 'Approved', value: data.approved, color: '#16a34a', bg: '#f0fdf4', border: 'rgba(34,197,94,0.2)' },
              { label: 'Pending',  value: data.pending,  color: '#2563eb', bg: '#eff6ff', border: 'rgba(37,99,235,0.2)'  },
              { label: 'Flagged',  value: data.rejected, color: '#dc2626', bg: '#fef2f2', border: 'rgba(220,38,38,0.2)'  },
            ].map(s => (
              <div key={s.label} style={{ textAlign: 'center', padding: '12px 8px', borderRadius: 10, background: s.bg, border: `1px solid ${s.border}` }}>
                <p style={{ fontSize: 22, fontWeight: 700, color: s.color, margin: 0 }}>{s.value}</p>
                <p style={{ fontSize: 11, color: s.color, margin: '2px 0 0', fontWeight: 600, opacity: 0.8 }}>{s.label}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <p style={{ fontSize: 12, color: '#94a3b8', textAlign: 'center' }}>
          {pct === 100
            ? 'All questions reviewed — ready to export.'
            : 'This page refreshes automatically every 30 seconds.'}
          {lastUpdated && (
            <> · Last updated {lastUpdated.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' })}</>
          )}
        </p>
      </div>

      <style>{`@keyframes spin { to { transform: rotate(360deg) } }`}</style>
    </div>
  )
}
