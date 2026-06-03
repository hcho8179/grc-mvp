import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'
import { useAuth } from '../context/AuthContext'
import { useTheme } from '../context/ThemeContext'
import { Icon } from '../components/Layout'
import { StatusBadge, GenerationBadge } from '../components/StatusBadge'
import { dueDateUrgency, formatDueDate } from '../utils/questionnaireMeta.js'

export default function QuestionnairsList() {
  const { t } = useTheme()
  const { user } = useAuth()
  const canDelete = user?.role === 'owner' || user?.role === 'admin'
  const [items, setItems] = useState([])
  const [page, setPage] = useState(1)
  const [meta, setMeta] = useState({ total: 0, pages: 1 })
  const [loading, setLoading] = useState(true)
  const nav = useNavigate()

  const load = (p = page) => {
    setLoading(true)
    api.getQuestionnaires(p)
      .then(data => { setItems(data.items); setMeta({ total: data.total, pages: data.pages }) })
      .catch(console.error)
      .finally(() => setLoading(false))
  }
  useEffect(() => { load(page) }, [page])

  const handleDelete = async (e, id) => {
    e.stopPropagation()
    if (!confirm('Delete this questionnaire and all its questions?')) return
    await api.deleteQuestionnaire(id)
    load()
  }

  return (
    <div className="h-full overflow-y-auto">
      <div className="p-8 max-w-6xl mx-auto">

        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold" style={{ color: t.text }}>Questionnaires</h1>
            <p className="text-sm mt-0.5" style={{ color: t.text2 }}>
              Upload, review, and export security questionnaires
            </p>
          </div>
          <button onClick={() => nav('/questionnaires/upload')}
                  className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold text-white hover:opacity-90 transition-all"
                  style={{ background: t.primary }}>
            <Icon name="upload" size={14} color="white" /> Upload Questionnaire
          </button>
        </div>

        {loading ? (
          <div className="space-y-2">
            {[...Array(4)].map((_, i) => <div key={i} className="skeleton h-14 rounded-xl" />)}
          </div>
        ) : items.length === 0 ? (
          <div className="rounded-xl py-20 text-center" style={t.card}>
            <div className="w-14 h-14 rounded-xl mx-auto mb-4 flex items-center justify-center"
                 style={{ background: t.dark ? 'rgba(59,130,246,0.1)' : '#eff6ff' }}>
              <Icon name="clipboard" size={28} color={t.primary} />
            </div>
            <p className="font-semibold mb-1" style={{ color: t.text }}>No questionnaires yet</p>
            <p className="text-sm mb-6" style={{ color: t.text3 }}>
              Upload an Excel questionnaire and get draft answers for every question.
            </p>
            <button onClick={() => nav('/questionnaires/upload')}
                    className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold text-white hover:opacity-90"
                    style={{ background: t.primary }}>
              <Icon name="plus" size={14} color="white" /> Upload your first questionnaire
            </button>
          </div>
        ) : (
          <>
            <div className="rounded-xl overflow-hidden" style={t.card}>
              <table className="w-full text-sm">
                <thead>
                  <tr style={{ background: t.tableHead, borderBottom: `1px solid ${t.borderColor}` }}>
                    {['Name', 'Customer', 'Status', 'AI', 'Questions', 'Due', 'Uploaded', ''].map(h => (
                      <th key={h} className="px-5 py-3 text-left text-xs font-semibold"
                          style={{ color: t.text3 }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {items.map(q => (
                    <tr key={q.id} className="cursor-pointer transition-colors group"
                        style={{ borderBottom: `1px solid ${t.borderColor}` }}
                        onClick={() => nav(`/questionnaires/${q.id}`)}
                        onMouseEnter={e => e.currentTarget.style.background = t.surfaceHover}
                        onMouseLeave={e => e.currentTarget.style.background = 'transparent'}>
                      <td className="px-5 py-4">
                        <p className="font-medium" style={{ color: t.text }}>{q.name}</p>
                        <p className="text-xs mt-0.5" style={{ color: t.text3 }}>
                          {q.source_filename}
                          {q.source_sheet_name ? ` · ${q.source_sheet_name}` : ''}
                        </p>
                      </td>
                      <td className="px-5 py-4 text-sm" style={{ color: t.text2 }}>{q.customer_name || '—'}</td>
                      <td className="px-5 py-4"><StatusBadge status={q.status} /></td>
                      <td className="px-5 py-4"><GenerationBadge status={q.generation_status} /></td>
                      <td className="px-5 py-4 font-semibold tabular-nums" style={{ color: t.text2 }}>{q.question_count}</td>
                      <td className="px-5 py-4 text-xs font-medium" style={{
                        color: dueDateUrgency(q.due_date, q.status) === 'overdue' ? '#ef4444'
                          : dueDateUrgency(q.due_date, q.status) === 'soon' ? '#f59e0b'
                          : t.text3,
                      }}>
                        {formatDueDate(q.due_date)}
                      </td>
                      <td className="px-5 py-4 text-xs" style={{ color: t.text3 }}>
                        {new Date(q.created_at).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })}
                      </td>
                      {canDelete && (
                        <td className="px-5 py-4 text-right" onClick={e => handleDelete(e, q.id)}>
                          <span className="text-xs font-medium transition-colors hover:text-red-500 cursor-pointer"
                                style={{ color: t.text3 }}>Delete</span>
                        </td>
                      )}
                      {!canDelete && <td />}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="flex items-center justify-between mt-3 px-1">
              <p className="text-xs" style={{ color: t.text3 }}>
                {meta.total} questionnaire{meta.total !== 1 ? 's' : ''}
              </p>
              {meta.pages > 1 && (
                <div className="flex items-center gap-1">
                  <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}
                          className="px-2.5 py-1 rounded-lg text-xs font-medium disabled:opacity-30 hover:opacity-70 transition-all"
                          style={{ background: t.dark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)', color: t.text2 }}>
                    ← Prev
                  </button>
                  <span className="text-xs px-2" style={{ color: t.text3 }}>
                    {page} / {meta.pages}
                  </span>
                  <button onClick={() => setPage(p => Math.min(meta.pages, p + 1))} disabled={page === meta.pages}
                          className="px-2.5 py-1 rounded-lg text-xs font-medium disabled:opacity-30 hover:opacity-70 transition-all"
                          style={{ background: t.dark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)', color: t.text2 }}>
                    Next →
                  </button>
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  )
}
