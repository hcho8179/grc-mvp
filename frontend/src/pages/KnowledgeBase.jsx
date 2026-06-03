import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../api'
import { useAuth } from '../context/AuthContext'
import { useTheme } from '../context/ThemeContext'
import { Icon } from '../components/Layout'
import { formatConfirmedDate, reviewBadge } from '../utils/documentFreshness.js'

const FILE_COLOR = {
  pdf:  { text: '#ef4444', bg: 'rgba(239,68,68,0.1)',  border: 'rgba(239,68,68,0.2)'  },
  docx: { text: '#3b82f6', bg: 'rgba(59,130,246,0.1)', border: 'rgba(59,130,246,0.2)' },
  xlsx: { text: '#22c55e', bg: 'rgba(34,197,94,0.1)',  border: 'rgba(34,197,94,0.2)'  },
}

export default function KnowledgeBase() {
  const { t } = useTheme()
  const { user } = useAuth()
  const canManage = user?.role === 'owner' || user?.role === 'admin'
  const nav = useNavigate()
  const [docs, setDocs] = useState([])
  const [page, setPage] = useState(1)
  const [meta, setMeta] = useState({ total: 0, pages: 1, stale_answer_count: 0 })
  const [loading, setLoading] = useState(true)
  const [replacing, setReplacing] = useState(null)
  const [actionNotice, setActionNotice] = useState(null)

  const load = (p = page) => {
    setLoading(true)
    api.getKnowledge(p)
      .then(data => {
        setDocs(data.items)
        setMeta({ total: data.total, pages: data.pages, stale_answer_count: data.stale_answer_count ?? 0 })
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }
  useEffect(() => { load(page) }, [page])

  const showStaleNotice = (res, actionLabel) => {
    const marked = res.stale_answers_marked ?? 0
    const total = res.stale_answer_count ?? 0
    if (marked > 0) {
      setActionNotice({
        type: 'stale',
        marked,
        total,
        message: `${actionLabel}: ${marked} approved answer${marked !== 1 ? 's' : ''} in your library may be outdated and need re-review.`,
      })
    } else {
      setActionNotice({ type: 'ok', message: `${actionLabel} completed.` })
    }
    setTimeout(() => setActionNotice(null), 12000)
  }

  const handleDelete = async (id, name) => {
    if (!confirm(`Delete "${name}" and all its chunks?\n\nApproved answers that cited this policy will be flagged for re-review.`)) return
    try {
      const res = await api.deleteKnowledge(id)
      showStaleNotice(res, 'Document deleted')
      load()
    } catch (err) {
      alert(err?.message || 'Delete failed')
    }
  }

  const handleReplace = async (id, name, file) => {
    if (!file) return
    if (!confirm(`Replace "${name}" with "${file.name}"?\n\nOld chunks are removed and re-embedded. Approved answers that cited this policy will be flagged for re-review.`)) return
    setReplacing(id)
    try {
      const fd = new FormData()
      fd.append('file', file)
      const res = await api.replaceKnowledge(id, fd)
      showStaleNotice(res, 'Policy replaced')
      load()
    } catch (err) {
      alert(err?.message || 'Replace failed — check file type (PDF or DOCX only)')
    } finally {
      setReplacing(null)
    }
  }

  const staleCount = meta.stale_answer_count ?? 0

  return (
    <div className="h-full overflow-y-auto">
      <div className="p-8 max-w-6xl mx-auto">

        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold" style={{ color: t.text }}>Knowledge Base</h1>
            <p className="text-sm mt-0.5" style={{ color: t.text2 }}>
              Policies power AI drafts. Replace files when content changes; age badges are reminders to confirm, not auto-expiry.
            </p>
          </div>
          <button onClick={() => nav('/knowledge/upload')}
                  className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold text-white hover:opacity-90 transition-all"
                  style={{ background: t.primary }}>
            <Icon name="upload" size={14} color="white" /> Upload Document
          </button>
        </div>

        {staleCount > 0 && (
          <div className="mb-4 px-4 py-3 rounded-xl flex flex-wrap items-center justify-between gap-3"
               style={{ background: 'rgba(245,158,11,0.08)', border: '1px solid rgba(245,158,11,0.3)' }}>
            <p className="text-sm font-medium" style={{ color: '#92400e' }}>
              {staleCount} approved answer{staleCount !== 1 ? 's' : ''} may be outdated — a source policy was updated or removed.
            </p>
            <Link to="/answers/library?stale=1"
                  className="text-xs font-semibold px-3 py-1.5 rounded-lg text-white hover:opacity-90"
                  style={{ background: '#d97706' }}>
              Review stale answers →
            </Link>
          </div>
        )}

        {actionNotice && (
          <div className="mb-4 px-4 py-3 rounded-xl text-sm font-medium flex flex-wrap items-center justify-between gap-2"
               style={actionNotice.type === 'stale'
                 ? { background: 'rgba(245,158,11,0.08)', border: '1px solid rgba(245,158,11,0.3)', color: '#92400e' }
                 : { background: 'rgba(34,197,94,0.08)', border: '1px solid rgba(34,197,94,0.25)', color: '#166534' }}>
            <span>{actionNotice.message}</span>
            {actionNotice.type === 'stale' && (
              <Link to="/answers/library?stale=1" className="text-xs font-semibold underline">
                Open answer library ({actionNotice.total} stale)
              </Link>
            )}
          </div>
        )}

        {loading ? (
          <div className="space-y-2">{[...Array(4)].map((_, i) => <div key={i} className="skeleton h-14 rounded-xl" />)}</div>
        ) : docs.length === 0 ? (
          <div className="rounded-xl py-20 text-center" style={t.card}>
            <div className="w-14 h-14 rounded-xl mx-auto mb-4 flex items-center justify-center"
                 style={{ background: t.dark ? 'rgba(59,130,246,0.1)' : '#eff6ff' }}>
              <Icon name="book" size={28} color={t.primary} />
            </div>
            <p className="font-semibold mb-1" style={{ color: t.text }}>Knowledge base is empty</p>
            <p className="text-sm mb-6" style={{ color: t.text3 }}>
              Upload security policies, SOC 2 reports, or past questionnaire answers.
            </p>
            <button onClick={() => nav('/knowledge/upload')}
                    className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold text-white hover:opacity-90"
                    style={{ background: t.primary }}>
              <Icon name="plus" size={14} color="white" /> Upload your first document
            </button>
          </div>
        ) : (
          <>
            <div className="rounded-xl overflow-hidden" style={t.card}>
              <table className="w-full text-sm">
                <thead>
                  <tr style={{ background: t.tableHead, borderBottom: `1px solid ${t.borderColor}` }}>
                    {['Document', 'Type', 'Chunks', 'Last confirmed', '', ''].map(h => (
                      <th key={h} className="px-5 py-3 text-left text-xs font-semibold" style={{ color: t.text3 }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {docs.map(d => {
                    const fc = FILE_COLOR[d.file_type] || FILE_COLOR.pdf
                    const stale = reviewBadge(d.content_updated_at, d.review_message)
                    return (
                      <tr key={d.id} className="transition-colors"
                          style={{ borderBottom: `1px solid ${t.borderColor}` }}
                          onMouseEnter={e => e.currentTarget.style.background = t.surfaceHover}
                          onMouseLeave={e => e.currentTarget.style.background = 'transparent'}>
                        <td className="px-5 py-4">
                          <div className="flex items-center gap-3">
                            <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
                                 style={{ background: fc.bg, border: `1px solid ${fc.border}` }}>
                              <Icon name="doc" size={14} color={fc.text} />
                            </div>
                            <div className="flex items-center gap-2 min-w-0">
                              <span className="font-medium truncate" style={{ color: t.text }}>
                                {d.filename}
                              </span>
                              {stale && (
                                <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-bold flex-shrink-0 cursor-default"
                                      title={stale.title}
                                      style={{ background: stale.bg, border: `1px solid ${stale.border}`, color: stale.color }}>
                                  ⚠ {stale.label}
                                </span>
                              )}
                            </div>
                          </div>
                        </td>
                        <td className="px-5 py-4">
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold uppercase"
                                style={{ background: fc.bg, border: `1px solid ${fc.border}`, color: fc.text }}>
                            {d.file_type}
                          </span>
                        </td>
                        <td className="px-5 py-4">
                          <span className="font-semibold tabular-nums" style={{ color: t.text }}>
                            {d.chunk_count}
                          </span>
                          <span className="text-xs ml-1" style={{ color: t.text3 }}>chunks</span>
                        </td>
                        <td className="px-5 py-4 text-xs" style={{ color: t.text3 }}
                            title="Upload or replace date — use Replace when the policy content changes">
                          {formatConfirmedDate(d.content_updated_at)}
                        </td>
                        <td className="px-5 py-4">
                          {canManage && (
                            <div className="flex items-center justify-end gap-3">
                              <label className="cursor-pointer text-xs font-medium transition-colors hover:opacity-70"
                                     style={{ color: t.primary }}
                                     title="Upload a new version — re-embeds chunks and flags linked library answers for re-review">
                                {replacing === d.id ? 'Replacing…' : 'Replace'}
                                <input type="file" accept=".pdf,.docx" className="hidden"
                                       disabled={replacing === d.id}
                                       onChange={e => { handleReplace(d.id, d.filename, e.target.files?.[0]); e.target.value = '' }} />
                              </label>
                              <button onClick={() => handleDelete(d.id, d.filename)}
                                      className="text-xs font-medium transition-colors hover:text-red-500"
                                      style={{ color: t.text3 }}>Delete</button>
                            </div>
                          )}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
            <p className="text-xs mt-3 px-1" style={{ color: t.text3 }}>
              Age badges (3mo / 6mo) mean “confirm still accurate” — they do not stop AI from using the document.
              When policy text changes, use <strong>Replace</strong> so linked approved answers are flagged automatically.
            </p>
            <div className="flex items-center justify-between mt-2 px-1">
              <p className="text-xs" style={{ color: t.text3 }}>
                {meta.total} document{meta.total !== 1 ? 's' : ''} · {docs.reduce((s, d) => s + d.chunk_count, 0)} chunks this page
              </p>
              {meta.pages > 1 && (
                <div className="flex items-center gap-1">
                  <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}
                          className="px-2.5 py-1 rounded-lg text-xs font-medium disabled:opacity-30 hover:opacity-70 transition-all"
                          style={{ background: t.dark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)', color: t.text2 }}>
                    ← Prev
                  </button>
                  <span className="text-xs px-2" style={{ color: t.text3 }}>{page} / {meta.pages}</span>
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
