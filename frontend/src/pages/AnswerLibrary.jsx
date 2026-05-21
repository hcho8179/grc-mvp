import { useState, useEffect } from 'react'
import { api } from '../api'
import { useTheme } from '../context/ThemeContext'
import { Icon } from '../components/Layout'

export default function AnswerLibrary() {
  const { t } = useTheme()
  const [data, setData] = useState({ answers: [], categories: [], total: 0, total_reuses: 0 })
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState('')

  useEffect(() => {
    setLoading(true)
    api.getAnswerLibrary(search, category).then(setData).catch(console.error).finally(() => setLoading(false))
  }, [search, category])

  return (
    <div className="h-full overflow-y-auto">
      <div className="p-8 max-w-6xl mx-auto">

        <div className="flex items-start justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold" style={{ color: t.text }}>Answer Library</h1>
            <p className="text-sm mt-0.5" style={{ color: t.text2 }}>
              <span className="font-semibold" style={{ color: t.text }}>{data.total}</span> approved answers ·{' '}
              <span className="font-semibold" style={{ color: t.text }}>{data.total_reuses}</span> total reuses
            </p>
          </div>
        </div>

        {/* Search */}
        <div className="flex gap-3 mb-5">
          <div className="relative flex-1 max-w-sm">
            <div className="absolute inset-y-0 left-3.5 flex items-center pointer-events-none">
              <Icon name="search" size={14} color={t.text3} />
            </div>
            <input value={search} onChange={e => setSearch(e.target.value)}
                   placeholder="Search questions or answers…"
                   className="w-full pl-10 pr-4 py-2.5 text-sm rounded-xl outline-none transition-all"
                   style={{ ...t.input }}
                   onFocus={e => e.target.style.boxShadow = `0 0 0 2px ${t.primary}40`}
                   onBlur={e => e.target.style.boxShadow = 'none'} />
          </div>
          {(search || category) && (
            <button onClick={() => { setSearch(''); setCategory('') }}
                    className="text-sm font-medium px-3 transition-opacity hover:opacity-70"
                    style={{ color: t.text3 }}>
              Clear
            </button>
          )}
        </div>

        {/* Category filters */}
        {data.categories.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-6">
            {[{ name: 'All', count: data.total, value: '' }, ...data.categories.map(c => ({ name: c.name, count: c.count, value: c.name }))].map(c => (
              <button key={c.value} onClick={() => setCategory(c.value)}
                      className="px-3 py-1.5 rounded-full text-xs font-semibold transition-all"
                      style={category === c.value
                        ? { background: t.primary, color: 'white' }
                        : { background: t.dark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)',
                            border: `1px solid ${t.borderColor}`, color: t.text2 }}>
                {c.name} ({c.count})
              </button>
            ))}
          </div>
        )}

        {loading ? (
          <div className="space-y-2">{[...Array(4)].map((_, i) => <div key={i} className="skeleton h-14 rounded-xl" />)}</div>
        ) : data.answers.length === 0 ? (
          <div className="rounded-xl py-20 text-center" style={t.card}>
            <div className="w-14 h-14 rounded-xl mx-auto mb-4 flex items-center justify-center"
                 style={{ background: t.dark ? 'rgba(59,130,246,0.1)' : '#eff6ff' }}>
              <Icon name="archive" size={28} color={t.primary} />
            </div>
            <p className="font-semibold mb-1" style={{ color: t.text }}>
              {search ? 'No answers match your search' : 'Answer library is empty'}
            </p>
            <p className="text-sm" style={{ color: t.text3 }}>
              {search ? 'Try a different search term.' : 'Approve answers in a questionnaire to build your library.'}
            </p>
          </div>
        ) : (
          <div className="rounded-xl overflow-hidden" style={t.card}>
            <table className="w-full text-sm">
              <thead>
                <tr style={{ background: t.tableHead, borderBottom: `1px solid ${t.borderColor}` }}>
                  {['Question', 'Answer', 'Category', 'Reuses', 'Added'].map(h => (
                    <th key={h} className="px-5 py-3 text-left text-xs font-semibold" style={{ color: t.text3 }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.answers.map(a => (
                  <tr key={a.id} className="align-top transition-colors"
                      style={{ borderBottom: `1px solid ${t.borderColor}` }}
                      onMouseEnter={e => e.currentTarget.style.background = t.surfaceHover}
                      onMouseLeave={e => e.currentTarget.style.background = 'transparent'}>
                    <td className="px-5 py-4 max-w-[200px]">
                      <p className="text-xs font-medium leading-relaxed line-clamp-3" style={{ color: t.text }}>{a.question_text}</p>
                    </td>
                    <td className="px-5 py-4 max-w-[300px]">
                      <p className="text-xs leading-relaxed line-clamp-4" style={{ color: t.text2 }}>{a.answer_text}</p>
                    </td>
                    <td className="px-5 py-4">
                      {a.answer_category ? (
                        <span className="inline-block px-2 py-0.5 rounded text-xs font-semibold"
                              style={{ background: t.dark ? 'rgba(59,130,246,0.1)' : '#eff6ff',
                                       color: t.primary,
                                       border: `1px solid ${t.dark ? 'rgba(59,130,246,0.2)' : 'rgba(59,130,246,0.3)'}` }}>
                          {a.answer_category}
                        </span>
                      ) : <span className="text-xs" style={{ color: t.text3 }}>—</span>}
                    </td>
                    <td className="px-5 py-4">
                      {a.times_reused > 0 ? (
                        <span className="inline-block px-2 py-0.5 rounded text-xs font-semibold tabular-nums"
                              style={{ background: 'rgba(34,197,94,0.1)', color: '#16a34a', border: '1px solid rgba(34,197,94,0.2)' }}>
                          {a.times_reused}
                        </span>
                      ) : <span className="text-xs" style={{ color: t.text3 }}>0</span>}
                    </td>
                    <td className="px-5 py-4 text-xs" style={{ color: t.text3 }}>
                      {new Date(a.created_at).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
