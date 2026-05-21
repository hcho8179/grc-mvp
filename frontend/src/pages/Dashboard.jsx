import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'
import { useTheme } from '../context/ThemeContext'
import { Icon } from '../components/Layout'
import { StatusBadge } from '../components/StatusBadge'

function StatCard({ label, value, sub, icon, accent }) {
  const { t } = useTheme()
  return (
    <div className="rounded-xl p-5 transition-all" style={t.card}>
      <div className="flex items-center justify-between mb-4">
        <p className="text-xs font-semibold" style={{ color: t.text3 }}>{label}</p>
        <div className="w-8 h-8 rounded-lg flex items-center justify-center"
             style={{ background: `${accent}18` }}>
          <Icon name={icon} size={15} color={accent} />
        </div>
      </div>
      <p className="text-3xl font-bold tabular-nums mb-1" style={{ color: t.text }}>{value}</p>
      {sub && <p className="text-xs" style={{ color: t.text3 }}>{sub}</p>}
    </div>
  )
}

export default function Dashboard() {
  const { t } = useTheme()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const nav = useNavigate()

  useEffect(() => {
    api.getDashboard().then(setData).catch(console.error).finally(() => setLoading(false))
  }, [])

  if (loading) return (
    <div className="h-full overflow-y-auto p-8">
      <div className="max-w-6xl mx-auto">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          {[...Array(4)].map((_, i) => <div key={i} className="skeleton h-28 rounded-xl" />)}
        </div>
        <div className="skeleton h-72 rounded-xl" />
      </div>
    </div>
  )

  const { total_questionnaires=0, total_answered=0, total_approved=0,
          avg_conf_pct=0, hours_saved=0, total_cost=0, recent=[] } = data || {}

  return (
    <div className="h-full overflow-y-auto">
      <div className="p-8 max-w-6xl mx-auto">

        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold" style={{ color: t.text }}>Dashboard</h1>
            <p className="text-sm mt-0.5" style={{ color: t.text2 }}>AI-powered security questionnaire automation</p>
          </div>
          <div className="flex gap-2">
            <button onClick={() => nav('/knowledge')}
                    className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all hover:opacity-80"
                    style={{ background: t.dark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)',
                             color: t.text2, border: `1px solid ${t.borderColor}` }}>
              <Icon name="upload" size={14} color={t.text2} /> Upload Policy
            </button>
            <button onClick={() => nav('/questionnaires/upload')}
                    className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold text-white transition-all hover:opacity-90"
                    style={{ background: t.primary }}>
              <Icon name="plus" size={14} color="white" /> New Questionnaire
            </button>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <StatCard label="Total Questionnaires" value={total_questionnaires} sub="All time" icon="clipboard" accent="#3b82f6" />
          <StatCard label="Answers Generated"    value={total_answered}        sub={`${total_approved} approved`} icon="check" accent="#22c55e" />
          <StatCard label="Avg Confidence"       value={`${avg_conf_pct}%`}    sub="AI match score" icon="spark" accent={avg_conf_pct >= 70 ? '#22c55e' : '#f59e0b'} />
          <StatCard label="Time Saved"           value={`${hours_saved}h`}     sub="@ 8 min per question" icon="clock" accent="#8b5cf6" />
        </div>

        {/* Recent questionnaires */}
        <div className="rounded-xl overflow-hidden" style={t.card}>
          <div className="px-5 py-4 flex items-center justify-between"
               style={{ borderBottom: `1px solid ${t.borderColor}` }}>
            <div>
              <h2 className="text-sm font-semibold" style={{ color: t.text }}>Recent Questionnaires</h2>
              <p className="text-xs mt-0.5" style={{ color: t.text3 }}>Click a row to open the review workspace</p>
            </div>
            <button onClick={() => nav('/questionnaires')}
                    className="text-xs font-semibold flex items-center gap-1 hover:underline"
                    style={{ color: t.primary }}>
              View all <Icon name="chevronR" size={12} color={t.primary} />
            </button>
          </div>

          {recent.length === 0 ? (
            <div className="py-16 text-center">
              <p className="text-sm font-medium mb-4" style={{ color: t.text3 }}>No questionnaires yet</p>
              <button onClick={() => nav('/questionnaires/upload')}
                      className="px-4 py-2 rounded-xl text-sm font-semibold text-white hover:opacity-90"
                      style={{ background: t.primary }}>
                Upload your first questionnaire
              </button>
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr style={{ background: t.tableHead, borderBottom: `1px solid ${t.borderColor}` }}>
                  {['Name', 'Customer', 'Status', 'Questions', 'Date'].map(h => (
                    <th key={h} className="px-5 py-3 text-left text-xs font-semibold"
                        style={{ color: t.text3 }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {recent.map(q => (
                  <tr key={q.id} className="cursor-pointer transition-colors group"
                      style={{ borderBottom: `1px solid ${t.borderColor}` }}
                      onClick={() => nav(`/questionnaires/${q.id}`)}
                      onMouseEnter={e => e.currentTarget.style.background = t.surfaceHover}
                      onMouseLeave={e => e.currentTarget.style.background = 'transparent'}>
                    <td className="px-5 py-3.5">
                      <span className="font-medium" style={{ color: t.text }}>{q.name}</span>
                    </td>
                    <td className="px-5 py-3.5 text-sm" style={{ color: t.text2 }}>{q.customer_name || '—'}</td>
                    <td className="px-5 py-3.5"><StatusBadge status={q.status} /></td>
                    <td className="px-5 py-3.5 font-semibold tabular-nums" style={{ color: t.text2 }}>{q.question_count}</td>
                    <td className="px-5 py-3.5 text-xs" style={{ color: t.text3 }}>
                      {new Date(q.created_at).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {total_cost > 0 && (
          <p className="text-xs mt-3 text-right" style={{ color: t.text3 }}>
            Total AI cost: ${total_cost.toFixed(4)}
          </p>
        )}
      </div>
    </div>
  )
}
