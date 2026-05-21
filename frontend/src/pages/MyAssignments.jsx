import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'
import { useTheme } from '../context/ThemeContext'
import { Icon } from '../components/Layout'
import { StatusBadge, ConfidenceBadge } from '../components/StatusBadge'

const STATUS_ORDER = { pending: 0, generated: 1, rejected: 2, approved: 3 }

export default function MyAssignments() {
  const { t } = useTheme()
  const nav = useNavigate()
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('open') // 'open' | 'all'

  useEffect(() => {
    api.getMyAssignments()
      .then(data => { setItems(data); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  const visible = filter === 'open'
    ? items.filter(q => q.status === 'pending' || q.status === 'generated')
    : items

  const sorted = [...visible].sort((a, b) =>
    (STATUS_ORDER[a.status] ?? 9) - (STATUS_ORDER[b.status] ?? 9)
  )

  const openCount = items.filter(q => q.status === 'pending' || q.status === 'generated').length

  return (
    <div className="p-8 max-w-3xl mx-auto" style={{ color: t.text }}>

      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold" style={{ color: t.text }}>My Assignments</h1>
          <p className="text-sm mt-0.5" style={{ color: t.text3 }}>
            Questions assigned to you across all questionnaires
          </p>
        </div>
        {openCount > 0 && (
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl text-sm font-semibold"
               style={{ background: t.dark ? 'rgba(245,158,11,0.1)' : '#fffbeb',
                        color: '#d97706',
                        border: '1px solid rgba(245,158,11,0.25)' }}>
            <Icon name="inbox" size={14} color="#d97706" />
            {openCount} open
          </div>
        )}
      </div>

      {/* Filter tabs */}
      <div className="flex gap-1 mb-5 p-1 rounded-xl w-fit"
           style={{ background: t.dark ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.05)' }}>
        {[
          { key: 'open', label: 'Open' },
          { key: 'all',  label: 'All' },
        ].map(opt => (
          <button key={opt.key}
                  onClick={() => setFilter(opt.key)}
                  className="px-4 py-1.5 rounded-lg text-sm font-semibold transition-all"
                  style={{
                    background: filter === opt.key
                      ? (t.dark ? t.surface : '#ffffff')
                      : 'transparent',
                    color: filter === opt.key ? t.text : t.text3,
                    boxShadow: filter === opt.key ? t.shadow : 'none',
                  }}>
            {opt.label}
          </button>
        ))}
      </div>

      {/* List */}
      {loading ? (
        <div className="space-y-3">
          {[1,2,3].map(i => <div key={i} className="skeleton h-20 rounded-xl" />)}
        </div>
      ) : sorted.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <div className="w-12 h-12 rounded-2xl flex items-center justify-center mb-4"
               style={{ background: t.dark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)' }}>
            <Icon name="inbox" size={22} color={t.text3} />
          </div>
          <p className="font-semibold mb-1" style={{ color: t.text }}>
            {filter === 'open' ? 'No open assignments' : 'No assignments yet'}
          </p>
          <p className="text-sm" style={{ color: t.text3 }}>
            {filter === 'open'
              ? 'All your assigned questions are answered.'
              : 'An owner or admin can assign questions to you from a questionnaire.'}
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          {sorted.map(item => (
            <button
              key={item.id}
              onClick={() => nav(`/questionnaires/${item.questionnaire_id}`)}
              className="w-full text-left rounded-xl p-4 transition-all hover:translate-y-[-1px]"
              style={{ ...t.card, cursor: 'pointer' }}
              onMouseEnter={e => e.currentTarget.style.boxShadow = t.shadowMd}
              onMouseLeave={e => e.currentTarget.style.boxShadow = t.card.boxShadow}>

              {/* Top row: questionnaire + status */}
              <div className="flex items-center gap-2 mb-2 flex-wrap">
                <span className="text-xs font-semibold px-2 py-0.5 rounded-md"
                      style={{ background: t.dark ? 'rgba(59,130,246,0.1)' : '#eff6ff',
                               color: t.primary }}>
                  {item.questionnaire_name}
                </span>
                {item.customer_name && (
                  <span className="text-xs" style={{ color: t.text3 }}>
                    · {item.customer_name}
                  </span>
                )}
                <div className="ml-auto flex items-center gap-2">
                  {item.confidence && item.status === 'generated' && (
                    <ConfidenceBadge confidence={item.confidence} />
                  )}
                  <StatusBadge status={item.status} />
                </div>
              </div>

              {/* Question text */}
              <p className="text-sm leading-relaxed line-clamp-2" style={{ color: t.text }}>
                {item.question_text}
              </p>

              {/* Draft answer preview if generated */}
              {item.draft_answer && (
                <p className="text-xs mt-2 leading-relaxed line-clamp-1 italic"
                   style={{ color: t.text3 }}>
                  Draft: {item.draft_answer}
                </p>
              )}

              <div className="flex items-center gap-1 mt-2">
                <span className="text-xs" style={{ color: t.text3 }}>
                  Click to open questionnaire →
                </span>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
