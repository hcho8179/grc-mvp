import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../api'
import { useTheme } from '../context/ThemeContext'
import { Icon } from '../components/Layout'

function HealthBar({ value, height = 6 }) {
  const color = value >= 75 ? '#16a34a' : value >= 50 ? '#d97706' : '#dc2626'
  return (
    <div className="w-full rounded-full overflow-hidden"
         style={{ height, background: 'rgba(128,128,128,0.12)' }}>
      <div className="h-full rounded-full transition-all duration-700"
           style={{ width: `${value}%`, background: color }} />
    </div>
  )
}

function HealthScore({ value, size = 'md' }) {
  const color = value >= 75 ? '#16a34a' : value >= 50 ? '#d97706' : '#dc2626'
  const bg    = value >= 75 ? 'rgba(34,197,94,0.1)' : value >= 50 ? 'rgba(245,158,11,0.1)' : 'rgba(239,68,68,0.1)'
  const border= value >= 75 ? 'rgba(34,197,94,0.25)' : value >= 50 ? 'rgba(245,158,11,0.25)' : 'rgba(239,68,68,0.25)'
  const label = value >= 75 ? 'Good' : value >= 50 ? 'Needs work' : 'Critical gap'
  if (size === 'lg') {
    return (
      <div className="flex flex-col items-center">
        <span className="text-5xl font-black" style={{ color }}>{value}</span>
        <span className="text-xs font-semibold mt-1" style={{ color }}>{label}</span>
      </div>
    )
  }
  return (
    <span className="text-xs font-bold px-2 py-0.5 rounded-md"
          style={{ background: bg, color, border: `1px solid ${border}` }}>
      {value} · {label}
    </span>
  )
}

export default function KBHealth() {
  const { t } = useTheme()
  const nav = useNavigate()
  const [data, setData] = useState(null)
  const [freshness, setFreshness] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      api.getKBHealth(),
      api.getKnowledgeFreshnessSummary().catch(() => null),
    ])
      .then(([kb, fr]) => { setData(kb); setFreshness(fr); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  const categories = data?.categories || []
  const criticalGaps = categories.filter(c => c.health < 50)

  return (
    <div className="p-8 max-w-4xl mx-auto" style={{ color: t.text }}>

      {/* Header */}
      <div className="flex items-start justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold mb-1" style={{ color: t.text }}>
            Knowledge Base Health
          </h1>
          <p className="text-sm" style={{ color: t.text3 }}>
            Shows which topics your KB covers well — and where to upload next.
          </p>
        </div>
        <button
          onClick={() => nav('/knowledge/upload')}
          className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold text-white hover:opacity-90 transition-all"
          style={{ background: t.primary }}>
          <Icon name="upload" size={14} color="white" />
          Upload Document
        </button>
      </div>

      {loading ? (
        <div className="space-y-4">
          <div className="skeleton h-32 rounded-2xl" />
          {[1,2,3,4].map(i => <div key={i} className="skeleton h-24 rounded-xl" />)}
        </div>
      ) : !data || data.total_questions === 0 ? (
        <div className="flex flex-col items-center justify-center py-24 text-center">
          <div className="w-14 h-14 rounded-2xl flex items-center justify-center mb-4"
               style={{ background: t.dark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)' }}>
            <Icon name="chart" size={26} color={t.text3} />
          </div>
          <p className="font-semibold text-lg mb-2" style={{ color: t.text }}>No data yet</p>
          <p className="text-sm max-w-xs" style={{ color: t.text3 }}>
            Draft answers on at least one questionnaire first — this page analyses the results.
          </p>
        </div>
      ) : (
        <>
          {freshness && (freshness.stale_answer_count > 0 || freshness.documents_needing_review?.length > 0) && (
            <div className="rounded-xl p-4 mb-6 space-y-3"
                 style={{ background: 'rgba(245,158,11,0.06)', border: '1px solid rgba(245,158,11,0.25)' }}>
              <p className="text-sm font-semibold" style={{ color: '#92400e' }}>Policy hygiene</p>
              {freshness.stale_answer_count > 0 && (
                <p className="text-xs" style={{ color: '#b45309' }}>
                  {freshness.stale_answer_count} approved answer{freshness.stale_answer_count !== 1 ? 's' : ''} need re-review after a policy change.{' '}
                  <Link to="/answers/library?stale=1" className="font-semibold underline">Review stale answers</Link>
                </p>
              )}
              {freshness.documents_needing_review?.length > 0 && (
                <div className="text-xs space-y-1" style={{ color: '#b45309' }}>
                  <p className="font-medium">Confirm these policies are still current (upload/replace resets the clock):</p>
                  <ul className="list-disc pl-4 space-y-0.5">
                    {freshness.documents_needing_review.slice(0, 5).map(d => (
                      <li key={d.id}>{d.filename} — {d.review_message}</li>
                    ))}
                  </ul>
                  {freshness.documents_needing_review.length > 5 && (
                    <Link to="/knowledge" className="font-semibold underline">View all in Knowledge Base</Link>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Overall score card */}
          <div className="rounded-2xl p-6 mb-6 flex items-center gap-8"
               style={{ ...t.card }}>
            <div className="flex-shrink-0">
              <HealthScore value={data.overall_health ?? 0} size="lg" />
            </div>
            <div className="flex-1">
              <p className="text-sm font-semibold mb-1" style={{ color: t.text }}>
                Overall KB Health
              </p>
              <HealthBar value={data.overall_health ?? 0} height={8} />
              <p className="text-xs mt-2" style={{ color: t.text3 }}>
                Based on {data.total_questions} answered questions across all questionnaires
              </p>
              {criticalGaps.length > 0 && (
                <p className="text-xs mt-2 font-semibold" style={{ color: '#dc2626' }}>
                  {criticalGaps.length} critical gap{criticalGaps.length > 1 ? 's' : ''} — see below
                </p>
              )}
            </div>
          </div>

          {/* Category cards */}
          <div className="space-y-3">
            {categories.map(c => {
              const scoreColor = c.avg_score == null ? t.text3
                : c.avg_score >= 0.85 ? '#16a34a'
                : c.avg_score >= 0.70 ? '#d97706'
                : '#dc2626'

              return (
                <div key={c.category} className="rounded-xl p-5"
                     style={{ ...t.card }}>
                  <div className="flex items-start gap-4">

                    {/* Health score circle */}
                    <div className="flex-shrink-0 w-12 h-12 rounded-xl flex items-center justify-center font-black text-lg"
                         style={{
                           background: c.health >= 75 ? 'rgba(34,197,94,0.1)'
                             : c.health >= 50 ? 'rgba(245,158,11,0.1)'
                             : 'rgba(239,68,68,0.1)',
                           color: c.health >= 75 ? '#16a34a' : c.health >= 50 ? '#d97706' : '#dc2626',
                         }}>
                      {c.health}
                    </div>

                    <div className="flex-1 min-w-0">
                      {/* Top row */}
                      <div className="flex items-center gap-3 mb-2 flex-wrap">
                        <span className="font-semibold text-sm" style={{ color: t.text }}>
                          {c.category}
                        </span>
                        <span className="text-xs" style={{ color: t.text3 }}>
                          {c.total} question{c.total !== 1 ? 's' : ''}
                        </span>
                        {c.avg_score != null && (
                          <span className="text-xs font-semibold" style={{ color: scoreColor }}>
                            avg match {Math.round(c.avg_score * 100)}%
                          </span>
                        )}
                        {c.no_source > 0 && (
                          <span className="text-xs font-semibold" style={{ color: '#dc2626' }}>
                            {c.no_source} with no source
                          </span>
                        )}
                      </div>

                      {/* Health bar */}
                      <HealthBar value={c.health} height={5} />

                      {/* Stats row */}
                      <div className="flex items-center gap-4 mt-2 flex-wrap">
                        <span className="text-[11px]" style={{ color: '#16a34a' }}>
                          ✓ {c.approved} approved
                        </span>
                        <span className="text-[11px]" style={{ color: '#ef4444' }}>
                          ✗ {c.rejected} rejected
                        </span>
                        {c.low_conf > 0 && (
                          <span className="text-[11px]" style={{ color: '#d97706' }}>
                            ⚠ {c.low_conf} low confidence
                          </span>
                        )}
                      </div>

                      {/* Upload recommendation if health is poor */}
                      {c.health < 65 && (
                        <div className="mt-3 flex items-center gap-2 px-3 py-2 rounded-lg"
                             style={{ background: t.dark ? 'rgba(239,68,68,0.06)' : '#fef2f2',
                                      border: '1px solid rgba(239,68,68,0.2)' }}>
                          <Icon name="upload" size={12} color="#dc2626" />
                          <p className="text-xs" style={{ color: '#dc2626' }}>
                            <span className="font-semibold">Fix this:</span> Upload a {c.upload_hint}
                          </p>
                          <button
                            onClick={() => nav('/knowledge/upload')}
                            className="ml-auto text-xs font-semibold hover:opacity-70 transition-opacity flex-shrink-0"
                            style={{ color: '#dc2626' }}>
                            Upload →
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </>
      )}
    </div>
  )
}
