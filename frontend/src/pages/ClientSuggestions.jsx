import { useState, useEffect, useMemo } from 'react'
import { api } from '../api'
import { useTheme } from '../context/ThemeContext'
import { Icon } from '../components/Layout'

export default function ClientSuggestions() {
  const { t } = useTheme()
  const [answers, setAnswers] = useState([])
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState(new Set())
  const [pulling, setPulling] = useState(false)
  const [toast, setToast] = useState(null)
  const [filterClient, setFilterClient] = useState('all')
  const [filterStatus, setFilterStatus] = useState('new') // 'new' | 'all'

  useEffect(() => {
    api.listClientAnswers()
      .then(setAnswers)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  const clients = useMemo(() => {
    const seen = new Map()
    answers.forEach(a => seen.set(a.client_workspace_id, a.client_name))
    return [...seen.entries()].map(([id, name]) => ({ id, name }))
  }, [answers])

  const visible = useMemo(() => answers.filter(a => {
    if (filterClient !== 'all' && a.client_workspace_id !== Number(filterClient)) return false
    if (filterStatus === 'new' && a.already_in_firm) return false
    return true
  }), [answers, filterClient, filterStatus])

  const allNewIds = visible.filter(a => !a.already_in_firm).map(a => a.id)
  const allSelected = allNewIds.length > 0 && allNewIds.every(id => selected.has(id))

  const toggle = (id) => setSelected(s => {
    const n = new Set(s)
    n.has(id) ? n.delete(id) : n.add(id)
    return n
  })

  const toggleAll = () => {
    if (allSelected) setSelected(new Set())
    else setSelected(new Set(allNewIds))
  }

  const handlePull = async () => {
    if (selected.size === 0) return
    setPulling(true)
    try {
      const { pulled, skipped } = await api.pullClientAnswers([...selected])
      setToast({ msg: `${pulled} answer${pulled !== 1 ? 's' : ''} added to firm library${skipped > 0 ? ` · ${skipped} skipped (already exists)` : ''}`, color: 'green' })
      setSelected(new Set())
      // Refresh
      const fresh = await api.listClientAnswers()
      setAnswers(fresh)
    } catch (err) {
      setToast({ msg: err.message, color: 'red' })
    } finally {
      setPulling(false)
    }
  }

  useEffect(() => {
    if (!toast) return
    const t = setTimeout(() => setToast(null), 4000)
    return () => clearTimeout(t)
  }, [toast])

  const inputCls = 'text-xs px-2.5 py-1.5 rounded-lg outline-none transition-all'

  return (
    <div className="h-full overflow-y-auto">
      <div className="p-8 max-w-6xl mx-auto">

        {/* Header */}
        <div className="flex items-start justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold" style={{ color: t.text }}>Client Suggestions</h1>
            <p className="text-sm mt-0.5" style={{ color: t.text2 }}>
              Answers your clients have approved — pick the reusable ones to add to your firm library.
            </p>
          </div>
          <button
            onClick={handlePull}
            disabled={selected.size === 0 || pulling}
            className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold text-white transition-all hover:opacity-90 disabled:opacity-40"
            style={{ background: t.primary }}>
            <Icon name="archive" size={14} color="white" />
            {pulling ? 'Adding…' : `Add to firm library${selected.size > 0 ? ` (${selected.size})` : ''}`}
          </button>
        </div>

        {/* Filters */}
        <div className="flex items-center gap-2 mb-4">
          <select
            value={filterClient}
            onChange={e => setFilterClient(e.target.value)}
            className={inputCls}
            style={{ ...t.input }}>
            <option value="all">All clients</option>
            {clients.map(c => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>

          <div className="flex gap-1 p-0.5 rounded-lg"
               style={{ background: t.dark ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.04)' }}>
            {[['New only', 'new'], ['Show all', 'all']].map(([label, val]) => (
              <button key={val} type="button" onClick={() => setFilterStatus(val)}
                      className="px-3 py-1 rounded-md text-xs font-semibold transition-all"
                      style={filterStatus === val
                        ? { background: t.primary, color: 'white' }
                        : { color: t.text3 }}>
                {label}
              </button>
            ))}
          </div>

          <span className="text-xs ml-auto" style={{ color: t.text3 }}>
            {visible.filter(a => !a.already_in_firm).length} new · {visible.filter(a => a.already_in_firm).length} already in library
          </span>
        </div>

        {/* Table */}
        {loading ? (
          <div className="space-y-2">
            {[...Array(5)].map((_, i) => <div key={i} className="skeleton h-14 rounded-xl" />)}
          </div>
        ) : visible.length === 0 ? (
          <div className="rounded-xl py-20 text-center" style={t.card}>
            <div className="w-14 h-14 rounded-xl mx-auto mb-4 flex items-center justify-center"
                 style={{ background: t.dark ? 'rgba(59,130,246,0.1)' : '#eff6ff' }}>
              <Icon name="inbox" size={28} color={t.primary} />
            </div>
            <p className="font-semibold mb-1" style={{ color: t.text }}>
              {filterStatus === 'new' ? 'No new suggestions' : 'No client answers yet'}
            </p>
            <p className="text-sm" style={{ color: t.text3 }}>
              {filterStatus === 'new'
                ? 'All client answers are already in your firm library.'
                : 'Client answers will appear here once they approve answers in their workspaces.'}
            </p>
          </div>
        ) : (
          <div className="rounded-xl overflow-hidden" style={t.card}>
            <table className="w-full text-sm">
              <thead>
                <tr style={{ background: t.tableHead, borderBottom: `1px solid ${t.borderColor}` }}>
                  <th className="px-4 py-3 w-8">
                    <input type="checkbox" checked={allSelected} onChange={toggleAll}
                           className="rounded cursor-pointer" />
                  </th>
                  {['Question', 'Answer', 'Client', 'Status', 'Date'].map(h => (
                    <th key={h} className="px-4 py-3 text-left text-xs font-semibold"
                        style={{ color: t.text3 }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {visible.map(a => (
                  <tr key={a.id}
                      className="transition-colors"
                      style={{
                        borderBottom: `1px solid ${t.borderColor}`,
                        opacity: a.already_in_firm ? 0.5 : 1,
                      }}
                      onMouseEnter={e => { if (!a.already_in_firm) e.currentTarget.style.background = t.surfaceHover }}
                      onMouseLeave={e => e.currentTarget.style.background = 'transparent'}>

                    <td className="px-4 py-3">
                      <input
                        type="checkbox"
                        checked={selected.has(a.id)}
                        disabled={a.already_in_firm}
                        onChange={() => toggle(a.id)}
                        className="rounded cursor-pointer disabled:cursor-not-allowed"
                      />
                    </td>

                    <td className="px-4 py-3 max-w-[280px]">
                      <p className="text-xs line-clamp-2" style={{ color: t.text }}>{a.question_text}</p>
                    </td>

                    <td className="px-4 py-3 max-w-[280px]">
                      <p className="text-xs line-clamp-2" style={{ color: t.text2 }}>{a.answer_text}</p>
                    </td>

                    <td className="px-4 py-3 whitespace-nowrap">
                      <span className="text-xs font-medium px-2 py-0.5 rounded-md"
                            style={{
                              background: t.dark ? 'rgba(59,130,246,0.12)' : 'rgba(37,99,235,0.08)',
                              color: t.primary,
                            }}>
                        {a.client_name}
                      </span>
                    </td>

                    <td className="px-4 py-3 whitespace-nowrap">
                      {a.already_in_firm ? (
                        <span className="text-xs font-medium flex items-center gap-1" style={{ color: '#16a34a' }}>
                          <span>✓</span> In library
                        </span>
                      ) : (
                        <span className="text-xs" style={{ color: t.text3 }}>New</span>
                      )}
                    </td>

                    <td className="px-4 py-3 whitespace-nowrap text-xs" style={{ color: t.text3 }}>
                      {new Date(a.created_at).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Toast */}
      {toast && (
        <div className="fixed bottom-6 right-6 z-50 flex items-center gap-2.5 px-4 py-3 rounded-xl text-sm font-semibold text-white shadow-2xl"
             style={{ background: toast.color === 'green' ? '#15803d' : '#b91c1c' }}>
          {toast.msg}
        </div>
      )}
    </div>
  )
}
