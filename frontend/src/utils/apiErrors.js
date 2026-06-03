/** Parse FastAPI JSON error bodies into user-visible messages. */

export function messageFromBody(data, fallback) {
  if (!data || typeof data !== 'object') return fallback
  const d = data.detail
  if (typeof d === 'string') return d
  if (Array.isArray(d)) {
    return d.map((x) => x.msg || JSON.stringify(x)).join(', ')
  }
  if (d && typeof d === 'object' && d.message) return d.message
  return data.error || fallback
}

export async function messageFromResponse(res, fallback) {
  try {
    return messageFromBody(await res.json(), fallback)
  } catch {
    return fallback
  }
}
