/** Shared questionnaire display helpers (align with API fields). */

export function formatDueDate(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return '—'
  return d.toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' })
}

export function dueDateInputFromIso(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return ''
  return d.toISOString().slice(0, 10)
}

/** @returns {'overdue'|'soon'|null} */
export function dueDateUrgency(iso, questionnaireStatus) {
  if (!iso || questionnaireStatus === 'complete') return null
  const days = (new Date(iso) - new Date()) / 86400000
  if (days < 0) return 'overdue'
  if (days <= 2) return 'soon'
  return null
}

export function dueDateColor(iso, questionnaireStatus) {
  const u = dueDateUrgency(iso, questionnaireStatus)
  if (u === 'overdue') return '#ef4444'
  if (u === 'soon') return '#f59e0b'
  return null
}

export function isoDueDateFromInput(yyyyMmDd) {
  if (!yyyyMmDd?.trim()) return null
  return `${yyyyMmDd.trim()}T23:59:59`
}
