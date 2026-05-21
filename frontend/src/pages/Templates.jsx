import { useState, useEffect } from 'react'
import { api } from '../api'
import { useAuth } from '../context/AuthContext'
import { useTheme } from '../context/ThemeContext'
import { Icon } from '../components/Layout'

export default function Templates() {
  const { t } = useTheme()
  const { user } = useAuth()
  const canDelete = user?.role === 'owner' || user?.role === 'admin'
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)

  const load = () => {
    setLoading(true)
    api.getTemplates().then(setItems).catch(console.error).finally(() => setLoading(false))
  }
  useEffect(load, [])

  return (
    <div className="h-full overflow-y-auto">
      <div className="p-8 max-w-6xl mx-auto">

        <div className="mb-8">
          <h1 className="text-2xl font-bold" style={{ color: t.text }}>Templates</h1>
          <p className="text-sm mt-0.5" style={{ color: t.text2 }}>
            Saved column layouts — suggested automatically when uploading for the same customer.
          </p>
        </div>

        {loading ? (
          <div className="space-y-2">{[...Array(3)].map((_, i) => <div key={i} className="skeleton h-14 rounded-xl" />)}</div>
        ) : items.length === 0 ? (
          <div className="rounded-xl py-20 text-center" style={t.card}>
            <div className="w-14 h-14 rounded-xl mx-auto mb-4 flex items-center justify-center"
                 style={{ background: t.dark ? 'rgba(59,130,246,0.1)' : '#eff6ff' }}>
              <Icon name="grid" size={28} color={t.primary} />
            </div>
            <p className="font-semibold mb-1" style={{ color: t.text }}>No templates yet</p>
            <p className="text-sm" style={{ color: t.text3 }}>
              Templates are created automatically when you upload a questionnaire.
            </p>
          </div>
        ) : (
          <div className="rounded-xl overflow-hidden" style={t.card}>
            <table className="w-full text-sm">
              <thead>
                <tr style={{ background: t.tableHead, borderBottom: `1px solid ${t.borderColor}` }}>
                  {['Name', 'Customer', 'Q col', 'A col', 'Merged', 'Used', 'Created', ''].map(h => (
                    <th key={h} className="px-5 py-3 text-left text-xs font-semibold" style={{ color: t.text3 }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {items.map(item => (
                  <tr key={item.id} className="transition-colors"
                      style={{ borderBottom: `1px solid ${t.borderColor}` }}
                      onMouseEnter={e => e.currentTarget.style.background = t.surfaceHover}
                      onMouseLeave={e => e.currentTarget.style.background = 'transparent'}>
                    <td className="px-5 py-4 font-medium" style={{ color: t.text }}>{item.name}</td>
                    <td className="px-5 py-4" style={{ color: t.text2 }}>{item.customer_name || '—'}</td>
                    <td className="px-5 py-4">
                      <span className="px-2 py-0.5 rounded font-mono text-xs font-semibold"
                            style={{ background: t.dark ? 'rgba(59,130,246,0.1)' : '#eff6ff',
                                     color: t.primary,
                                     border: `1px solid ${t.dark ? 'rgba(59,130,246,0.2)' : 'rgba(59,130,246,0.3)'}` }}>
                        {item.question_col}
                      </span>
                    </td>
                    <td className="px-5 py-4">
                      {item.answer_col !== null ? (
                        <span className="px-2 py-0.5 rounded font-mono text-xs font-semibold"
                              style={{ background: t.dark ? 'rgba(139,92,246,0.1)' : '#f5f3ff',
                                       color: '#7c3aed',
                                       border: `1px solid ${t.dark ? 'rgba(139,92,246,0.2)' : 'rgba(139,92,246,0.3)'}` }}>
                          {item.answer_col}
                        </span>
                      ) : <span className="text-xs" style={{ color: t.text3 }}>—</span>}
                    </td>
                    <td className="px-5 py-4">
                      {item.merged_ranges > 0 ? (
                        <span className="text-xs font-semibold" style={{ color: '#d97706' }}>{item.merged_ranges}</span>
                      ) : <span className="text-xs" style={{ color: t.text3 }}>0</span>}
                    </td>
                    <td className="px-5 py-4">
                      {item.times_used > 0 ? (
                        <span className="inline-block px-2 py-0.5 rounded text-xs font-semibold tabular-nums"
                              style={{ background: 'rgba(34,197,94,0.1)', color: '#16a34a', border: '1px solid rgba(34,197,94,0.2)' }}>
                          {item.times_used}×
                        </span>
                      ) : <span className="text-xs" style={{ color: t.text3 }}>0</span>}
                    </td>
                    <td className="px-5 py-4 text-xs" style={{ color: t.text3 }}>
                      {new Date(item.created_at).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })}
                    </td>
                    <td className="px-5 py-4 text-right">
                      {canDelete && (
                        <button onClick={async () => { if (confirm(`Delete template "${item.name}"?`)) { await api.deleteTemplate(item.id); load() } }}
                                className="text-xs font-medium transition-colors hover:text-red-500"
                                style={{ color: t.text3 }}>Delete</button>
                      )}
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
