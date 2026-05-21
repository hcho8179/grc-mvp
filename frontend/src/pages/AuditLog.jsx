import { useEffect, useState } from 'react'
import { api } from '../api'
import { useTheme } from '../context/ThemeContext'
import { Icon } from '../components/Layout'

const ACTION_META = {
  'auth.login':              { label: 'Login',                  color: '#3b82f6', dot: '#3b82f6' },
  'auth.register':           { label: 'Register',               color: '#3b82f6', dot: '#3b82f6' },
  'questionnaire.uploaded':  { label: 'Questionnaire uploaded',  color: '#8b5cf6', dot: '#8b5cf6' },
  'questionnaire.exported':  { label: 'Questionnaire exported',  color: '#8b5cf6', dot: '#8b5cf6' },
  'questionnaire.deleted':   { label: 'Questionnaire deleted',   color: '#ef4444', dot: '#ef4444' },
  'answer.generated':        { label: 'AI answer generated',     color: '#22c55e', dot: '#22c55e' },
  'question.approved':       { label: 'Answer approved',         color: '#22c55e', dot: '#22c55e' },
  'question.bulk_approved':  { label: 'Bulk approved',           color: '#22c55e', dot: '#22c55e' },
  'question.rejected':       { label: 'Answer flagged',          color: '#ef4444', dot: '#ef4444' },
  'question.edited':         { label: 'Answer edited',           color: '#f59e0b', dot: '#f59e0b' },
  'document.uploaded':       { label: 'Document uploaded',       color: '#6366f1', dot: '#6366f1' },
  'document.deleted':        { label: 'Document deleted',        color: '#ef4444', dot: '#ef4444' },
}

const FILTER_OPTIONS = [
  { value: '', label: 'All events' },
  ...Object.entries(ACTION_META).map(([value, { label }]) => ({ value, label })),
]

function fmtTime(iso) {
  const d = new Date(iso)
  return d.toLocaleString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

export default function AuditLog() {
  const { t } = useTheme()
  const [events, setEvents] = useState([])
  const [filter, setFilter] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    api.getAuditLog(filter)
      .then(data => { setEvents(Array.isArray(data) ? data : []); setLoading(false) })
      .catch(() => setLoading(false))
  }, [filter])

  return (
    <div className="h-full overflow-y-auto">
      <div className="p-8 max-w-4xl mx-auto">

        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold" style={{ color: t.text }}>Audit Log</h1>
            <p className="text-sm mt-0.5" style={{ color: t.text2 }}>
              Every action taken in your workspace
            </p>
          </div>
          <select value={filter} onChange={e => setFilter(e.target.value)}
                  className="text-sm rounded-xl px-3 py-2 outline-none"
                  style={{ ...t.input, color: t.text2 }}>
            {FILTER_OPTIONS.map(o => (
              <option key={o.value} value={o.value}
                      style={{ background: t.dark ? '#161b27' : '#ffffff' }}>
                {o.label}
              </option>
            ))}
          </select>
        </div>

        {loading ? (
          <div className="space-y-2">{[...Array(6)].map((_, i) => <div key={i} className="skeleton h-12 rounded-xl" />)}</div>
        ) : events.length === 0 ? (
          <div className="rounded-xl py-20 text-center" style={t.card}>
            <Icon name="clock" size={32} color={t.text3} />
            <p className="mt-4 text-sm font-medium" style={{ color: t.text3 }}>No events yet.</p>
          </div>
        ) : (
          <div className="rounded-xl overflow-hidden" style={t.card}>
            <table className="w-full text-sm">
              <thead>
                <tr style={{ background: t.tableHead, borderBottom: `1px solid ${t.borderColor}` }}>
                  {['Event', 'User', 'Details', 'Time'].map(h => (
                    <th key={h} className="px-5 py-3 text-left text-xs font-semibold" style={{ color: t.text3 }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {events.map(e => {
                  const meta = ACTION_META[e.action] || { label: e.action, color: t.text3, dot: t.text3 }
                  const detail = Object.entries(e.detail || {})
                    .filter(([k]) => k !== 'questionnaire_id')
                    .map(([k, v]) => `${k}: ${v}`)
                    .join(' · ')
                  return (
                    <tr key={e.id} className="transition-colors"
                        style={{ borderBottom: `1px solid ${t.borderColor}` }}
                        onMouseEnter={el => el.currentTarget.style.background = t.surfaceHover}
                        onMouseLeave={el => el.currentTarget.style.background = 'transparent'}>
                      <td className="px-5 py-3.5">
                        <div className="flex items-center gap-2">
                          <div className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: meta.dot }} />
                          <span className="text-xs font-semibold" style={{ color: meta.color }}>{meta.label}</span>
                        </div>
                      </td>
                      <td className="px-5 py-3.5 text-xs" style={{ color: t.text2 }}>
                        {e.user_email || '—'}
                      </td>
                      <td className="px-5 py-3.5 text-xs font-mono" style={{ color: t.text3 }}>
                        {detail || '—'}
                      </td>
                      <td className="px-5 py-3.5 text-xs flex-shrink-0" style={{ color: t.text3 }}>
                        {fmtTime(e.created_at)}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}

        {events.length > 0 && (
          <p className="text-xs mt-3 text-center" style={{ color: t.text3 }}>
            {events.length} most recent event{events.length !== 1 ? 's' : ''}
          </p>
        )}
      </div>
    </div>
  )
}
