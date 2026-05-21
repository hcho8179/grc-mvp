import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'
import { useAuth } from '../context/AuthContext'
import { useTheme } from '../context/ThemeContext'
import { Icon } from '../components/Layout'

const FILE_COLOR = {
  pdf:  { text: '#ef4444', bg: 'rgba(239,68,68,0.1)',  border: 'rgba(239,68,68,0.2)'  },
  docx: { text: '#3b82f6', bg: 'rgba(59,130,246,0.1)', border: 'rgba(59,130,246,0.2)' },
  xlsx: { text: '#22c55e', bg: 'rgba(34,197,94,0.1)',  border: 'rgba(34,197,94,0.2)'  },
}

export default function KnowledgeBase() {
  const { t } = useTheme()
  const { user } = useAuth()
  const canDelete = user?.role === 'owner' || user?.role === 'admin'
  const nav = useNavigate()
  const [docs, setDocs] = useState([])
  const [page, setPage] = useState(1)
  const [meta, setMeta] = useState({ total: 0, pages: 1 })
  const [loading, setLoading] = useState(true)

  const load = (p = page) => {
    setLoading(true)
    api.getKnowledge(p)
      .then(data => {
        setDocs([...data.items].sort((a, b) => a.is_starter - b.is_starter))
        setMeta({ total: data.total, pages: data.pages })
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }
  useEffect(() => { load(page) }, [page])

  const handleDelete = async (id, name) => {
    if (!confirm(`Delete "${name}" and all its chunks?`)) return
    await api.deleteKnowledge(id)
    load()
  }

  return (
    <div className="h-full overflow-y-auto">
      <div className="p-8 max-w-6xl mx-auto">

        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold" style={{ color: t.text }}>Knowledge Base</h1>
            <p className="text-sm mt-0.5" style={{ color: t.text2 }}>
              Policies and documents that power suggested answers
            </p>
          </div>
          <button onClick={() => nav('/knowledge/upload')}
                  className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold text-white hover:opacity-90 transition-all"
                  style={{ background: t.primary }}>
            <Icon name="upload" size={14} color="white" /> Upload Document
          </button>
        </div>

        {/* Banner shown when user only has starter templates — prompt to upload real policies */}
        {!loading && docs.length > 0 && docs.every(d => d.is_starter) && (
          <div className="mb-6 flex items-start gap-3 rounded-xl px-5 py-4"
               style={{ background: 'rgba(245,158,11,0.08)', border: '1px solid rgba(245,158,11,0.3)' }}>
            <span className="text-xl flex-shrink-0 mt-0.5">⚠</span>
            <div>
              <p className="font-semibold text-sm mb-0.5" style={{ color: '#92400e' }}>
                You're running on starter templates
              </p>
              <p className="text-xs mb-3" style={{ color: '#b45309' }}>
                Your answers are based on generic policy templates, not your company's actual policies.
                Upload your real security policies to get accurate, company-specific answers.
              </p>
              <button onClick={() => nav('/knowledge/upload')}
                      className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold text-white hover:opacity-90"
                      style={{ background: '#d97706' }}>
                <Icon name="upload" size={12} color="white" /> Upload Your Policies
              </button>
            </div>
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
                    {['Document', 'Type', 'Chunks', 'Uploaded', '', ''].map(h => (
                      <th key={h} className="px-5 py-3 text-left text-xs font-semibold" style={{ color: t.text3 }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {docs.map(d => {
                    const fc = FILE_COLOR[d.file_type] || FILE_COLOR.pdf
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
                            <div>
                              <span className="font-medium" style={{ color: t.text }}>
                                {d.is_starter ? d.filename.replace('[Starter] ', '').replace('.txt', '') : d.filename}
                              </span>
                            </div>
                          </div>
                        </td>
                        <td className="px-5 py-4">
                          {d.is_starter ? (
                            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold"
                                  style={{ background: 'rgba(139,92,246,0.1)', border: '1px solid rgba(139,92,246,0.25)', color: '#8b5cf6' }}>
                              Starter
                            </span>
                          ) : (
                            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold uppercase"
                                  style={{ background: fc.bg, border: `1px solid ${fc.border}`, color: fc.text }}>
                              {d.file_type}
                            </span>
                          )}
                        </td>
                        <td className="px-5 py-4">
                          <span className="font-semibold tabular-nums" style={{ color: t.text }}>
                            {d.chunk_count}
                          </span>
                          <span className="text-xs ml-1" style={{ color: t.text3 }}>chunks</span>
                        </td>
                        <td className="px-5 py-4 text-xs" style={{ color: t.text3 }}>
                          {new Date(d.created_at).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })}
                        </td>
                        <td className="px-5 py-4 text-right">
                          {canDelete && (
                            <button onClick={() => handleDelete(d.id, d.filename)}
                                    className="text-xs font-medium transition-colors hover:text-red-500"
                                    style={{ color: t.text3 }}>Delete</button>
                          )}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
            <div className="flex items-center justify-between mt-3 px-1">
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
