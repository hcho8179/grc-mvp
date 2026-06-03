/** Policy freshness nudges — aligned with app/services/document_freshness.py */

export const REVIEW_WARN_DAYS = 90
export const REVIEW_URGENT_DAYS = 180

export function daysSince(dateStr) {
  if (!dateStr) return null
  return Math.floor((Date.now() - new Date(dateStr)) / 86_400_000)
}

/** @returns {'warn'|'urgent'|null} */
export function reviewLevel(dateStr) {
  const days = daysSince(dateStr)
  if (days == null) return null
  if (days >= REVIEW_URGENT_DAYS) return 'urgent'
  if (days >= REVIEW_WARN_DAYS) return 'warn'
  return null
}

export function reviewBadge(dateStr, serverMessage = null) {
  const level = reviewLevel(dateStr)
  if (!level) return null
  const days = daysSince(dateStr)
  const label = days >= 180 ? '6mo+' : '3mo+'
  const styles = {
    warn: {
      color: '#f59e0b',
      bg: 'rgba(245,158,11,0.1)',
      border: 'rgba(245,158,11,0.2)',
      title: serverMessage || 'Not confirmed in 3+ months — verify this policy is still current',
    },
    urgent: {
      color: '#ef4444',
      bg: 'rgba(239,68,68,0.1)',
      border: 'rgba(239,68,68,0.2)',
      title: serverMessage || 'Not confirmed in 6+ months — consider uploading a refreshed version',
    },
  }
  return { level, label, ...styles[level] }
}

export function formatConfirmedDate(dateStr) {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
}
