import { useState, useEffect } from 'react'
import { api } from '../api'
import { useTheme } from '../context/ThemeContext'
import { useAuth } from '../context/AuthContext'
import { Icon } from '../components/Layout'

export default function Trash() {
  const { t } = useTheme()
  const { user } = useAuth()
  const canRestore = user?.role === 'owner' || user?.role === 'admin'

  const [data, setData] = useState({ questionnaires: [], documents: [] })
  const [loading, setLoading] = useState(true)
  const [restoring, setRestoring] = useState(null)

  const load = () => {
    setLoading(true)
    api.getTrash()
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false))
  }
  useEffect(load, [])

  const handleRestore = async (type, id, name) => {
    if (!confirm(`Restore "${name}"?`)) return
    setRestoring(id)
    try {
      if (type === 'questionnaire') await api.restoreQuestionnaire(id)
      else await api.restoreDocument(id)
      load()
    } catch (e) {
      alert(e.message || 'Restore failed')
    }
    setRestoring(null)
  }

  const fmt = (iso) => new Date(iso).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
  const total = data.questionnaires.length + data.documents.length

  return (
    <div className="h-full overflow-y-auto">
      <div className="p-8 max-w-4xl mx-auto">

        <div className="mb-8">
          <h1 className="text-2xl font-bold" style={{ color: t.text }}>Trash</h1>
          <p className="text-sm mt-0.5" style={{ color: t.text2 }}>
            Deleted items — restore to recover, or they stay here indefinitely.
          </p>
        </div>

        {loading ? (
          <div className="space-y-2">{[...Array(3)].map((_, i) => <div key={i} className="skeleton h-14 rounded-xl" />)}</div>
        ) : total === 0 ? (
          <div className="rounded-xl py-20 text-center" style={t.card}>
            <div className="w-14 h-14 rounded-xl mx-auto mb-4 flex items-center justify-center"
                 style={{ background: t.dark ? 'rgba(255,255,255,0.06)' : '#f1f5f9' }}>
              <Icon name="check" size={26} color={t.text3} />
            </div>
            <p className="font-semibold mb-1" style={{ color: t.text }}>Trash is empty</p>
            <p className="text-sm" style={{ color: t.text3 }}>Nothing has been deleted.</p>
          </div>
        ) : (
          <div className="space-y-6">

            {data.questionnaires.length > 0 && (
              <div>
                <p className="text-xs font-semibold mb-2 px-1" style={{ color: t.text3 }}>
                  QUESTIONNAIRES ({data.questionnaires.length})
                </p>
                <div className="rounded-xl overflow-hidden" style={t.card}>
                  {data.questionnaires.map((q, i) => (
                    <div key={q.id}
                         className="flex items-center justify-between px-5 py-4"
                         style={{ borderBottom: i < data.questionnaires.length - 1 ? `1px solid ${t.borderColor}` : 'none' }}>
                      <div>
                        <p className="font-medium text-sm" style={{ color: t.text }}>{q.name}</p>
                        <p className="text-xs mt-0.5" style={{ color: t.text3 }}>
                          {q.question_count} questions · deleted {fmt(q.deleted_at)}
                        </p>
                      </div>
                      {canRestore && (
                        <button
                          onClick={() => handleRestore('questionnaire', q.id, q.name)}
                          disabled={restoring === q.id}
                          className="px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all hover:opacity-80 disabled:opacity-40"
                          style={{ background: 'rgba(22,163,74,0.1)', color: '#16a34a', border: '1px solid rgba(22,163,74,0.25)' }}>
                          {restoring === q.id ? 'Restoring…' : 'Restore'}
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {data.documents.length > 0 && (
              <div>
                <p className="text-xs font-semibold mb-2 px-1" style={{ color: t.text3 }}>
                  DOCUMENTS ({data.documents.length})
                </p>
                <div className="rounded-xl overflow-hidden" style={t.card}>
                  {data.documents.map((d, i) => (
                    <div key={d.id}
                         className="flex items-center justify-between px-5 py-4"
                         style={{ borderBottom: i < data.documents.length - 1 ? `1px solid ${t.borderColor}` : 'none' }}>
                      <div>
                        <p className="font-medium text-sm" style={{ color: t.text }}>{d.filename}</p>
                        <p className="text-xs mt-0.5" style={{ color: t.text3 }}>
                          {d.chunk_count} chunks · deleted {fmt(d.deleted_at)}
                        </p>
                      </div>
                      {canRestore && (
                        <button
                          onClick={() => handleRestore('document', d.id, d.filename)}
                          disabled={restoring === d.id}
                          className="px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all hover:opacity-80 disabled:opacity-40"
                          style={{ background: 'rgba(22,163,74,0.1)', color: '#16a34a', border: '1px solid rgba(22,163,74,0.25)' }}>
                          {restoring === d.id ? 'Restoring…' : 'Restore'}
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

          </div>
        )}
      </div>
    </div>
  )
}
