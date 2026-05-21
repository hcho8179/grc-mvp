import { useState, useEffect } from 'react'
import { api } from '../api'
import { useTheme } from '../context/ThemeContext'
import { Icon } from '../components/Layout'

function StatCard({ label, value, sub, icon, accent }) {
  const { t } = useTheme()
  return (
    <div className="rounded-xl p-5" style={t.card}>
      <div className="flex items-center justify-between mb-4">
        <p className="text-xs font-semibold" style={{ color: t.text3 }}>{label}</p>
        <div className="w-8 h-8 rounded-lg flex items-center justify-center"
             style={{ background: `${accent}18` }}>
          <Icon name={icon} size={14} color={accent} />
        </div>
      </div>
      <p className="text-3xl font-bold tabular-nums mb-1" style={{ color: t.text }}>{value}</p>
      {sub && <p className="text-xs" style={{ color: t.text3 }}>{sub}</p>}
    </div>
  )
}

export default function UsagePage() {
  const { t } = useTheme()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.getUsage().then(setData).catch(console.error).finally(() => setLoading(false))
  }, [])

  if (loading) return (
    <div className="h-full overflow-y-auto p-8">
      <div className="max-w-6xl mx-auto">
        <div className="grid grid-cols-4 gap-4 mb-6">{[...Array(4)].map((_, i) => <div key={i} className="skeleton h-28 rounded-xl" />)}</div>
        <div className="skeleton h-64 rounded-xl" />
      </div>
    </div>
  )

  const { month_label='', month_calls=0, month_input=0, month_output=0, month_cost=0,
          total_calls=0, total_input=0, total_output=0, total_cost=0, per_questionnaire=[] } = data || {}

  return (
    <div className="h-full overflow-y-auto">
      <div className="p-8 max-w-6xl mx-auto">

        <div className="mb-8">
          <h1 className="text-2xl font-bold" style={{ color: t.text }}>AI Usage</h1>
          <p className="text-sm mt-0.5" style={{ color: t.text2 }}>
            {month_label} · Token and cost tracking
          </p>
        </div>

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <StatCard label="LLM Calls"     value={month_calls.toLocaleString()}   sub="this month" icon="clock"  accent="#64748b" />
          <StatCard label="Input Tokens"  value={month_input.toLocaleString()}   sub="this month" icon="doc"    accent={t.primary} />
          <StatCard label="Output Tokens" value={month_output.toLocaleString()}  sub="this month" icon="spark"  accent="#8b5cf6" />
          <StatCard label="Cost"          value={`$${month_cost.toFixed(4)}`}    sub="this month" icon="bolt"   accent="#22c55e" />
        </div>

        <div className="rounded-xl overflow-hidden" style={t.card}>
          <div className="px-5 py-4" style={{ borderBottom: `1px solid ${t.borderColor}` }}>
            <h2 className="text-sm font-semibold" style={{ color: t.text }}>Cost by Questionnaire</h2>
            <p className="text-xs mt-0.5" style={{ color: t.text3 }}>All-time breakdown</p>
          </div>
          {per_questionnaire.length === 0 ? (
            <p className="px-5 py-12 text-center text-sm" style={{ color: t.text3 }}>No LLM calls recorded yet.</p>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr style={{ background: t.tableHead, borderBottom: `1px solid ${t.borderColor}` }}>
                  {['Questionnaire', 'Calls', 'Input', 'Output', 'Cost'].map(h => (
                    <th key={h} className="px-5 py-3 text-left text-xs font-semibold" style={{ color: t.text3 }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {per_questionnaire.map((r, i) => (
                  <tr key={i} className="transition-colors"
                      style={{ borderBottom: `1px solid ${t.borderColor}` }}
                      onMouseEnter={e => e.currentTarget.style.background = t.surfaceHover}
                      onMouseLeave={e => e.currentTarget.style.background = 'transparent'}>
                    <td className="px-5 py-4 font-medium" style={{ color: t.text }}>{r.name}</td>
                    <td className="px-5 py-4 tabular-nums" style={{ color: t.text2 }}>{r.calls}</td>
                    <td className="px-5 py-4 tabular-nums" style={{ color: t.text2 }}>{r.input_tokens.toLocaleString()}</td>
                    <td className="px-5 py-4 tabular-nums" style={{ color: t.text2 }}>{r.output_tokens.toLocaleString()}</td>
                    <td className="px-5 py-4">
                      <span className="text-xs font-semibold tabular-nums px-2 py-0.5 rounded"
                            style={{ background: 'rgba(34,197,94,0.1)', color: '#16a34a', border: '1px solid rgba(34,197,94,0.2)' }}>
                        ${r.cost.toFixed(4)}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        <p className="text-xs mt-4" style={{ color: t.text3 }}>
          All-time: <strong style={{ color: t.text2 }}>{total_calls.toLocaleString()}</strong> calls ·{' '}
          <strong style={{ color: t.text2 }}>{total_input.toLocaleString()}</strong> input ·{' '}
          <strong style={{ color: t.text2 }}>{total_output.toLocaleString()}</strong> output ·{' '}
          <strong style={{ color: '#16a34a' }}>${total_cost.toFixed(4)}</strong> total
        </p>
      </div>
    </div>
  )
}
