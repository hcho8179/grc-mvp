import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { api } from '../api'

const STATUS_META = {
  pending: { label: 'Pending', color: '#64748b', bg: '#f8fafc', border: '#e2e8f0' },
  generated: { label: 'Drafted', color: '#2563eb', bg: '#eff6ff', border: '#bfdbfe' },
  approved: { label: 'Approved', color: '#16a34a', bg: '#f0fdf4', border: '#bbf7d0' },
  rejected: { label: 'Flagged', color: '#dc2626', bg: '#fef2f2', border: '#fecaca' },
}

const CONFIDENCE_META = {
  high: { label: 'High', color: '#15803d', bg: '#f0fdf4', border: '#bbf7d0' },
  medium: { label: 'Medium', color: '#b45309', bg: '#fffbeb', border: '#fde68a' },
  low: { label: 'Low', color: '#dc2626', bg: '#fef2f2', border: '#fecaca' },
}

function Badge({ meta }) {
  if (!meta) return null
  return (
    <span style={{
      display: 'inline-flex',
      alignItems: 'center',
      padding: '3px 8px',
      borderRadius: 999,
      border: `1px solid ${meta.border}`,
      background: meta.bg,
      color: meta.color,
      fontSize: 11,
      fontWeight: 700,
      whiteSpace: 'nowrap',
    }}>
      {meta.label}
    </span>
  )
}

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
      <div style={{ textAlign: 'center', padding: 40 }}>
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
  const questions = Array.isArray(data.questions) ? data.questions : []

  return (
    <div style={{ minHeight: '100vh', background: '#f8fafc', fontFamily: 'system-ui, sans-serif', color: '#0f172a' }}>
      <div style={{ maxWidth: 1120, margin: '0 auto', padding: '48px 24px' }}>
        <div style={{ marginBottom: 28 }}>
          <span style={{ background: '#2563eb', color: 'white', padding: '5px 12px', borderRadius: 8, fontSize: 13, fontWeight: 700 }}>
            Greenlight
          </span>
        </div>

        <header style={{ display: 'flex', justifyContent: 'space-between', gap: 24, alignItems: 'flex-end', marginBottom: 24, flexWrap: 'wrap' }}>
          <div>
            {data.customer_name && (
              <p style={{ fontSize: 13, color: '#64748b', margin: '0 0 4px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                {data.customer_name}
              </p>
            )}
            <h1 style={{ fontSize: 28, fontWeight: 750, color: '#0f172a', margin: 0, lineHeight: 1.2 }}>
              {data.name}
            </h1>
            <p style={{ fontSize: 13, color: '#64748b', margin: '8px 0 0' }}>
              Read-only questionnaire review
              {lastUpdated && <> · Updated {lastUpdated.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' })}</>}
            </p>
          </div>
          <div style={{ minWidth: 220 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
              <span style={{ fontSize: 12, fontWeight: 700, color: '#475569' }}>Review progress</span>
              <span style={{ fontSize: 22, fontWeight: 800, color: barColor }}>{pct}%</span>
            </div>
            <div style={{ height: 8, borderRadius: 999, background: '#e2e8f0', overflow: 'hidden' }}>
              <div style={{ height: '100%', width: `${pct}%`, background: barColor, transition: 'width 0.5s ease' }} />
            </div>
          </div>
        </header>

        <section style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
          gap: 12,
          marginBottom: 20,
        }}>
          {[
            { label: 'Approved', value: data.approved, color: '#16a34a', bg: '#f0fdf4', border: '#bbf7d0' },
            { label: 'Pending', value: data.pending, color: '#2563eb', bg: '#eff6ff', border: '#bfdbfe' },
            { label: 'Flagged', value: data.rejected, color: '#dc2626', bg: '#fef2f2', border: '#fecaca' },
            { label: 'Total', value: data.total, color: '#475569', bg: '#ffffff', border: '#e2e8f0' },
          ].map(s => (
            <div key={s.label} style={{ padding: '14px 16px', borderRadius: 10, background: s.bg, border: `1px solid ${s.border}` }}>
              <p style={{ fontSize: 24, fontWeight: 800, color: s.color, margin: 0 }}>{s.value}</p>
              <p style={{ fontSize: 12, color: s.color, margin: '2px 0 0', fontWeight: 700 }}>{s.label}</p>
            </div>
          ))}
        </section>

        <section style={{ background: 'white', border: '1px solid #e2e8f0', borderRadius: 12, overflow: 'hidden', boxShadow: '0 1px 3px rgba(15,23,42,0.06)' }}>
          <div style={{ padding: '14px 18px', borderBottom: '1px solid #e2e8f0', background: '#ffffff' }}>
            <p style={{ fontSize: 13, color: '#475569', fontWeight: 700, margin: 0 }}>Questions and answers</p>
          </div>

          {questions.length === 0 ? (
            <div style={{ padding: 32, textAlign: 'center', color: '#64748b', fontSize: 14 }}>No questions are available yet.</div>
          ) : (
            <div>
              {questions.map(q => (
                <article key={q.id} style={{ padding: '18px', borderBottom: '1px solid #e2e8f0' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap', marginBottom: 10 }}>
                    <span style={{ fontSize: 12, fontWeight: 800, color: '#2563eb', background: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: 7, padding: '3px 7px' }}>
                      Q{q.index}
                    </span>
                    <Badge meta={STATUS_META[q.status]} />
                    <Badge meta={CONFIDENCE_META[q.confidence]} />
                    {q.short_answer && (
                      <span style={{ fontSize: 11, fontWeight: 800, color: '#334155', background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 999, padding: '3px 8px' }}>
                        {q.short_answer}
                      </span>
                    )}
                  </div>
                  <p style={{ margin: '0 0 12px', fontSize: 14, fontWeight: 700, lineHeight: 1.45, color: '#0f172a' }}>
                    {q.question_text}
                  </p>
                  {q.answer ? (
                    <div style={{ fontSize: 13, lineHeight: 1.6, color: '#334155', background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 10, padding: '12px 14px', whiteSpace: 'pre-wrap' }}>
                      {q.answer}
                    </div>
                  ) : (
                    <p style={{ margin: 0, fontSize: 13, color: '#94a3b8' }}>No draft answer yet.</p>
                  )}
                </article>
              ))}
            </div>
          )}
        </section>

        <p style={{ fontSize: 12, color: '#94a3b8', textAlign: 'center', marginTop: 18 }}>
          This page is read-only and refreshes automatically every 30 seconds.
        </p>
      </div>

      <style>{`@keyframes spin { to { transform: rotate(360deg) } }`}</style>
    </div>
  )
}
