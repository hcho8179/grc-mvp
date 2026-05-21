/** Clean, minimal status and confidence badges. */

export function StatusBadge({ status }) {
  const map = {
    draft:       { dot: '#64748b', text: '#64748b', bg: 'rgba(100,116,139,0.1)', border: 'rgba(100,116,139,0.2)', label: 'Draft'       },
    in_progress: { dot: '#f59e0b', text: '#f59e0b', bg: 'rgba(245,158,11,0.1)',  border: 'rgba(245,158,11,0.2)',  label: 'In Progress', pulse: true },
    complete:    { dot: '#22c55e', text: '#22c55e', bg: 'rgba(34,197,94,0.1)',   border: 'rgba(34,197,94,0.2)',   label: 'Complete'    },
    pending:     { dot: '#64748b', text: '#94a3b8', bg: 'rgba(100,116,139,0.08)',border: 'rgba(100,116,139,0.15)',label: 'Pending'     },
    generated:   { dot: '#3b82f6', text: '#3b82f6', bg: 'rgba(59,130,246,0.1)',  border: 'rgba(59,130,246,0.2)',  label: 'Drafted'     },
    approved:    { dot: '#22c55e', text: '#16a34a', bg: 'rgba(34,197,94,0.1)',   border: 'rgba(34,197,94,0.2)',   label: 'Approved'    },
    rejected:    { dot: '#ef4444', text: '#ef4444', bg: 'rgba(239,68,68,0.1)',   border: 'rgba(239,68,68,0.2)',   label: 'Flagged'     },
  }
  const c = map[status] || map.draft
  return (
    <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-xs font-semibold"
          style={{ background: c.bg, border: `1px solid ${c.border}`, color: c.text }}>
      <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${c.pulse ? 'animate-pulse' : ''}`}
            style={{ background: c.dot }} />
      {c.label}
    </span>
  )
}

export function ConfidenceBadge({ confidence }) {
  const map = {
    high:   { dot: '#22c55e', text: '#15803d', bg: 'rgba(34,197,94,0.1)',  border: 'rgba(34,197,94,0.2)',  label: 'High'   },
    medium: { dot: '#f59e0b', text: '#d97706', bg: 'rgba(245,158,11,0.1)', border: 'rgba(245,158,11,0.2)', label: 'Medium' },
    low:    { dot: '#ef4444', text: '#dc2626', bg: 'rgba(239,68,68,0.1)',  border: 'rgba(239,68,68,0.2)',  label: 'Low'    },
  }
  if (!confidence) return null
  const c = map[confidence] || map.medium
  return (
    <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-xs font-semibold"
          style={{ background: c.bg, border: `1px solid ${c.border}`, color: c.text }}>
      <span className="w-1.5 h-1.5 rounded-full flex-shrink-0" style={{ background: c.dot }} />
      {c.label}
    </span>
  )
}
