import { useState, useEffect, useRef, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api } from '../api'
import { useTheme } from '../context/ThemeContext'
import { useAuth } from '../context/AuthContext'
import { Icon } from '../components/Layout'
import { StatusBadge, ConfidenceBadge, GenerationBadge } from '../components/StatusBadge'
import {
  dueDateInputFromIso,
  dueDateUrgency,
  formatDueDate,
  isoDueDateFromInput,
} from '../utils/questionnaireMeta.js'

// Returns true if the answer text contains no client-specific signals.
// Used to auto-detect whether an answer can be promoted to generic.
function detectIsGeneric(answerText, customerName) {
  if (!answerText || !customerName) return false
  const text = answerText.toLowerCase()
  const client = customerName.toLowerCase().trim()

  // Client name appears in answer
  if (client.length > 2 && text.includes(client)) return false

  // Specific cloud regions — AWS, Azure, GCP
  if (/\b(us-east|us-west|eu-west|eu-central|ap-southeast|ap-northeast|ap-south|ca-central|sa-east)-\d\b/.test(text)) return false
  if (/\b(eastus2?|westus[23]?|westeurope|northeurope|southeastasia|australiaeast|australiasoutheast)\b/.test(text)) return false
  if (/\b(us-central1|us-east[14]|europe-west\d|asia-east[12]|australia-southeast\d)\b/.test(text)) return false

  // IP addresses / CIDR ranges
  if (/\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(\/\d+)?\b/.test(text)) return false

  // Specific URLs
  if (/https?:\/\//.test(text)) return false

  // Specific headcounts ("50 employees", "200 staff")
  if (/\b\d+\s*(employees|staff|contractors|personnel|team members|fte|headcount)\b/i.test(answerText)) return false

  return true
}

// ── Toast ─────────────────────────────────────────────────────────────────
function Toast({ msg, color, onDone }) {
  useEffect(() => { const t = setTimeout(onDone, 3200); return () => clearTimeout(t) }, [onDone])
  const bg = color === 'green' ? '#15803d' : color === 'red' ? '#b91c1c' : '#1d4ed8'
  return (
    <div className="toast-anim fixed bottom-6 right-6 z-50 flex items-center gap-2.5
                    px-4 py-3 rounded-xl text-sm font-semibold text-white shadow-2xl"
         style={{ background: bg, border: '1px solid rgba(255,255,255,0.15)' }}>
      {msg}
    </div>
  )
}

// ── Sources panel ─────────────────────────────────────────────────────────
function ScoreBadge({ score }) {
  if (score == null) return null
  const pct   = Math.round(score * 100)
  const color = score >= 0.85 ? '#16a34a' : score >= 0.70 ? '#d97706' : '#dc2626'
  const bg    = score >= 0.85 ? 'rgba(34,197,94,0.1)' : score >= 0.70 ? 'rgba(245,158,11,0.1)' : 'rgba(239,68,68,0.1)'
  const border= score >= 0.85 ? 'rgba(34,197,94,0.25)' : score >= 0.70 ? 'rgba(245,158,11,0.25)' : 'rgba(239,68,68,0.25)'
  const label = score >= 0.85 ? 'Strong match' : score >= 0.70 ? 'Partial match' : 'Weak match'
  const tip   = score >= 0.85
    ? 'This source closely matched the question — answer is well grounded.'
    : score >= 0.70
    ? 'This source partially matched — review the answer before approving.'
    : 'Weak match — loosely related text found. Verify manually or assign to a subject expert.'
  return (
    <span className="flex items-center gap-1.5 text-[10px] font-semibold px-2 py-0.5 rounded-md flex-shrink-0 cursor-default"
          style={{ background: bg, color, border: `1px solid ${border}` }}
          title={tip}>
      {label}
      <span className="opacity-60 font-normal">{pct}%</span>
    </span>
  )
}

function SourcesPanel({ citedChunks, t }) {
  const [chunks, setChunks] = useState({})
  const [loading, setLoading] = useState(false)

  const ids = citedChunks?.map(c => c.id) || []
  const scoreMap = Object.fromEntries((citedChunks || []).map(c => [c.id, c.score]))

  useEffect(() => {
    if (!ids.length) return
    setLoading(true)
    const results = {}
    Promise.all(ids.map(async id => {
      try { results[id] = await api.getChunk(id) } catch { results[id] = null }
    })).then(() => { setChunks(results); setLoading(false) })
  }, [ids.join(',')])

  if (!ids.length) return null
  return (
    <div className="mt-4 pt-4" style={{ borderTop: `1px solid ${t.borderColor}` }}>
      <p className="text-xs font-semibold mb-2 flex items-center gap-1.5" style={{ color: t.text3 }}>
        <Icon name="doc" size={11} color={t.text3} />
        {ids.length} source{ids.length !== 1 ? 's' : ''}
      </p>
      <div className="space-y-2">
        {loading && <div className="skeleton h-14 rounded-lg" />}
        {!loading && ids.map(id => {
          const c = chunks[id]
          const score = scoreMap[id]
          const reviewWarn = c?.review_level === 'warn' || c?.review_level === 'urgent'
          const dateLabel = c?.content_updated_at
            ? new Date(c.content_updated_at).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
            : null
          return (
            <div key={id} className="rounded-lg p-3"
                 style={{ background: t.dark ? 'rgba(59,130,246,0.05)' : '#eff6ff',
                          border: `1px solid ${reviewWarn ? 'rgba(245,158,11,0.4)' : (t.dark ? 'rgba(59,130,246,0.15)' : 'rgba(59,130,246,0.2)')}` }}>
              <div className="flex items-center gap-2 mb-1.5">
                <span className="text-xs font-semibold truncate" style={{ color: t.primary }}>
                  {c?.source_document || `Source #${id}`}
                </span>
                {c?.source_section && (
                  <span className="text-[10px]" style={{ color: t.text3 }}>
                    {c.source_section}
                  </span>
                )}
                <div className="ml-auto flex-shrink-0 flex items-center gap-1.5">
                  {dateLabel && (
                    <span className="text-[10px] font-medium flex items-center gap-1"
                          style={{ color: reviewWarn ? '#b45309' : t.text3 }}
                          title={c?.review_message || `Last confirmed ${dateLabel}`}>
                      {reviewWarn && '⚠ '}Confirmed {dateLabel}
                    </span>
                  )}
                  <ScoreBadge score={score} />
                </div>
              </div>
              {reviewWarn && c?.review_message && (
                <p className="text-[10px] mb-1.5" style={{ color: '#b45309' }}>{c.review_message}</p>
              )}
              {c?.text && (
                <p className="text-xs leading-relaxed italic pl-3"
                   style={{ color: t.text2, borderLeft: `2px solid ${t.primary}40` }}>
                  "{c.text.substring(0, 280)}{c.text.length > 280 ? '…' : ''}"
                </p>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

// ── Reasoning panel ───────────────────────────────────────────────────────
function ReasoningPanel({ reasoning, t }) {
  if (!reasoning) return null
  return (
    <div className="mt-4 pt-4" style={{ borderTop: `1px solid ${t.borderColor}` }}>
      <div className="rounded-lg p-3 text-xs leading-relaxed"
           style={{ background: t.dark ? 'rgba(245,158,11,0.06)' : '#fffbeb',
                    border: `1px solid ${t.dark ? 'rgba(245,158,11,0.15)' : 'rgba(245,158,11,0.3)'}`,
                    color: t.text2 }}>
        <p className="font-semibold mb-1.5 flex items-center gap-1.5" style={{ color: '#d97706' }}>
          <Icon name="spark" size={11} color="#d97706" /> Reasoning
        </p>
        {reasoning}
      </div>
    </div>
  )
}

// ── Comments panel ────────────────────────────────────────────────────────
function CommentsPanel({ questionnaireId, questionId, currentUser, t }) {
  const [comments, setComments] = useState([])
  const [body, setBody] = useState('')
  const [posting, setPosting] = useState(false)

  useEffect(() => {
    api.getComments(questionnaireId, questionId)
      .then(setComments)
      .catch(() => {})
  }, [questionnaireId, questionId])

  const handlePost = async () => {
    if (!body.trim()) return
    setPosting(true)
    try {
      const c = await api.postComment(questionnaireId, questionId, body.trim())
      setComments(p => [...p, c])
      setBody('')
    } catch {}
    setPosting(false)
  }

  const handleDelete = async (cId) => {
    try {
      await api.deleteComment(questionnaireId, questionId, cId)
      setComments(p => p.filter(c => c.id !== cId))
    } catch {}
  }

  const fmt = (iso) => {
    const d = new Date(iso)
    return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' }) +
           ' ' + d.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' })
  }

  return (
    <div className="mt-4 pt-4" style={{ borderTop: `1px solid ${t.borderColor}` }}>
      <p className="text-xs font-semibold mb-3 flex items-center gap-1.5" style={{ color: t.text3 }}>
        <Icon name="chat" size={11} color={t.text3} />
        Comments {comments.length > 0 && `(${comments.length})`}
      </p>
      <div className="space-y-2 mb-3">
        {comments.map(c => (
          <div key={c.id} className="rounded-lg p-3"
               style={{ background: t.dark ? 'rgba(255,255,255,0.03)' : '#f9fafb',
                        border: `1px solid ${t.borderColor}` }}>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-semibold" style={{ color: t.text }}>
                {c.user_name || c.user_email}
              </span>
              <span className="text-[10px] ml-auto" style={{ color: t.text3 }}>{fmt(c.created_at)}</span>
              {(c.user_id === currentUser?.id || currentUser?.role === 'owner' || currentUser?.role === 'admin') && (
                <button
                  onClick={() => handleDelete(c.id)}
                  className="text-[10px] hover:opacity-70 transition-opacity ml-1"
                  style={{ color: '#ef4444' }}
                  title="Delete comment">
                  ✕
                </button>
              )}
            </div>
            <p className="text-xs leading-relaxed" style={{ color: t.text2 }}>{c.body}</p>
          </div>
        ))}
      </div>
      <div className="flex gap-2">
        <input
          value={body}
          onChange={e => setBody(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handlePost() } }}
          placeholder="Add a comment…"
          className="flex-1 rounded-lg px-3 py-2 text-xs outline-none"
          style={{ ...t.input, color: t.text }}
        />
        <button
          onClick={handlePost}
          disabled={posting || !body.trim()}
          className="px-3 py-2 rounded-lg text-xs font-semibold text-white disabled:opacity-40 transition-all hover:opacity-90"
          style={{ background: t.primary }}>
          {posting ? '…' : 'Post'}
        </button>
      </div>
    </div>
  )
}

// ── Flag + note ─────────────────────────────────────────────────────────────
function FlagNote({ q, questionnaireId, onFlagged, t }) {
  const [open, setOpen] = useState(false)
  const [note, setNote] = useState(q.flag_note || '')
  const [saving, setSaving] = useState(false)
  const ref = useRef(null)
  const inputRef = useRef(null)
  const isFlagged = !!q.flag_note

  useEffect(() => {
    const handler = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false) }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  useEffect(() => {
    setNote(q.flag_note || '')
  }, [q.id, q.flag_note])

  useEffect(() => {
    if (open) setTimeout(() => inputRef.current?.focus(), 50)
  }, [open])

  const save = async (newNote) => {
    setSaving(true)
    try {
      const updated = await api.flagQuestion(questionnaireId, q.id, newNote || null)
      onFlagged(updated)
    } catch {}
    setSaving(false)
  }

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen(o => !o)}
        className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium transition-all"
        style={{
          background: isFlagged ? 'rgba(245,158,11,0.1)' : (t.dark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)'),
          color: isFlagged ? '#d97706' : t.text3,
          border: `1px solid ${isFlagged ? 'rgba(245,158,11,0.4)' : t.borderColor}`,
        }}>
        <span style={{ fontSize: 12 }}>{isFlagged ? '⚑' : '⚐'}</span>
        {isFlagged ? 'Flagged' : 'Flag'}
      </button>
      {open && (
        <div className="absolute right-0 top-full mt-1 z-50 rounded-xl shadow-2xl p-3 w-64"
             style={{ background: t.surface, border: `1px solid ${t.borderColor}` }}>
          <p className="text-xs font-semibold mb-2" style={{ color: t.text }}>Add a note (e.g. "asked DevOps via Slack")</p>
          <textarea
            ref={inputRef}
            value={note}
            onChange={e => setNote(e.target.value)}
            rows={2}
            placeholder="What are you waiting on?"
            className="w-full text-xs rounded-lg px-3 py-2 resize-none outline-none mb-2"
            style={{ ...t.input }}
          />
          <div className="flex gap-2">
            <button
              onClick={() => { save(note); setOpen(false) }}
              disabled={saving}
              className="flex-1 py-1.5 rounded-lg text-xs font-semibold text-white transition-opacity hover:opacity-90 disabled:opacity-50"
              style={{ background: '#d97706' }}>
              {saving ? '…' : (isFlagged ? 'Update' : 'Flag')}
            </button>
            {isFlagged && (
              <button
                onClick={() => { save(null); setNote(''); setOpen(false) }}
                disabled={saving}
                className="px-3 py-1.5 rounded-lg text-xs font-semibold transition-opacity hover:opacity-70"
                style={{ background: t.dark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)', color: t.text3 }}>
                Clear
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

// ── Version history panel ────────────────────────────────────────────────
function VersionHistoryPanel({ questionnaireId, questionId, t }) {
  const [open, setOpen] = useState(false)
  const [versions, setVersions] = useState([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!open) return
    setLoading(true)
    api.getQuestionHistory(questionnaireId, questionId)
      .then(d => setVersions(d.versions))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [open, questionId])

  const ACTION_STYLE = {
    approved: { color: '#16a34a', label: 'Approved' },
    rejected: { color: '#dc2626', label: 'Rejected' },
    edited:   { color: '#6b7280', label: 'Edited' },
  }

  return (
    <div className="mt-4 pt-4" style={{ borderTop: `1px solid ${t.borderColor}` }}>
      <button
        onClick={() => setOpen(o => !o)}
        className="flex items-center gap-1.5 text-xs font-semibold mb-2 hover:opacity-70 transition-opacity"
        style={{ color: t.text3 }}>
        <span style={{ display: 'inline-block', transform: open ? 'rotate(90deg)' : 'none', transition: 'transform 0.15s' }}>▶</span>
        Edit history
      </button>
      {open && (
        <div className="space-y-2">
          {loading && <div className="skeleton h-10 rounded-lg" />}
          {!loading && versions.length === 0 && (
            <p className="text-xs" style={{ color: t.text3 }}>No recorded edits yet.</p>
          )}
          {!loading && versions.map(v => {
            const s = ACTION_STYLE[v.action] || ACTION_STYLE.edited
            return (
              <div key={v.id} className="rounded-lg px-3 py-2.5"
                   style={{ background: t.dark ? 'rgba(255,255,255,0.03)' : '#f9fafb',
                            border: `1px solid ${t.borderColor}` }}>
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-[10px] font-bold uppercase tracking-wide" style={{ color: s.color }}>{s.label}</span>
                  <span className="text-[10px]" style={{ color: t.text3 }}>
                    {v.user_name || v.user_email} · {new Date(v.created_at).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                  </span>
                  {v.short_answer && (
                    <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded"
                          style={{ background: 'rgba(59,130,246,0.1)', color: '#3b82f6' }}>
                      {v.short_answer}
                    </span>
                  )}
                </div>
                {v.draft_answer && (
                  <p className="text-xs leading-relaxed line-clamp-3" style={{ color: t.text2 }}>{v.draft_answer}</p>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

// ── Question detail panel (right side) ───────────────────────────────────
function QuestionDetail({ q, qIdx, questionnaireId, customerName, onApprove, onReject, onRegen, onFlagged, animClass, t }) {
  const { user: currentUser } = useAuth()
  const isCompany = currentUser?.workspace_type === 'company'
  const [answer, setAnswer] = useState(q.draft_answer || '')
  const [saving, setSaving] = useState(false)
  const [regening, setRegening] = useState(false)
  const [makeGeneric, setMakeGeneric] = useState(() => isCompany || detectIsGeneric(q.draft_answer || '', customerName))
  const saveTimer = useRef(null)
  const userEdited = useRef(false)

  // Reset everything when switching to a different question
  useEffect(() => {
    userEdited.current = false
    setAnswer(q.draft_answer || '')
    setMakeGeneric(isCompany || detectIsGeneric(q.draft_answer || '', customerName))
  }, [q.id])

  // Sync draft answer arriving from polling — but don't overwrite user's own edits
  useEffect(() => {
    if (!userEdited.current && q.draft_answer) {
      setAnswer(q.draft_answer)
      setMakeGeneric(isCompany || detectIsGeneric(q.draft_answer, customerName))
    }
  }, [q.draft_answer])

  const handleChange = (val) => {
    userEdited.current = true
    setAnswer(val)
    clearTimeout(saveTimer.current)
    saveTimer.current = setTimeout(async () => {
      setSaving(true)
      try { await api.updateQuestion(questionnaireId, q.id, val) } catch {}
      setSaving(false)
    }, 800)
  }

  const canAct = q.status === 'pending' || q.status === 'generated'

  return (
    <div className={`h-full flex flex-col ${animClass || ''}`}>
      {/* Question header */}
      <div className="px-8 py-5 flex-shrink-0"
           style={{ borderBottom: `1px solid ${t.borderColor}` }}>
        <div className="flex items-center gap-3 mb-3 flex-wrap">
          <span className="text-xs font-bold px-2.5 py-1 rounded-lg font-mono"
                style={{ background: t.dark ? 'rgba(59,130,246,0.1)' : '#eff6ff',
                         color: t.primary,
                         border: `1px solid ${t.dark ? 'rgba(59,130,246,0.2)' : 'rgba(59,130,246,0.3)'}` }}>
            Q{qIdx + 1}
          </span>
          {q.confidence && <ConfidenceBadge confidence={q.confidence} />}
          {q.short_answer && (
            <span className="px-2 py-0.5 rounded text-[10px] font-bold"
                  style={{
                    background: q.short_answer === 'Yes' ? 'rgba(22,163,74,0.12)' : q.short_answer === 'No' ? 'rgba(239,68,68,0.1)' : 'rgba(245,158,11,0.1)',
                    color: q.short_answer === 'Yes' ? '#16a34a' : q.short_answer === 'No' ? '#dc2626' : '#d97706',
                    border: `1px solid ${q.short_answer === 'Yes' ? 'rgba(22,163,74,0.25)' : q.short_answer === 'No' ? 'rgba(239,68,68,0.2)' : 'rgba(245,158,11,0.25)'}`,
                  }}>
              {q.short_answer}
            </span>
          )}
          <StatusBadge status={q.status} />
          <div className="ml-auto flex items-center gap-2">
            <FlagNote q={q} questionnaireId={questionnaireId} onFlagged={onFlagged} t={t} />
            {saving && <span className="text-xs" style={{ color: t.text3 }}>Saving…</span>}
          </div>
        </div>
        <p className="text-base font-medium leading-relaxed" style={{ color: t.text }}>
          {q.question_text}
        </p>
      </div>

      {/* Answer + panels */}
      <div className="flex-1 overflow-y-auto px-8 py-5">
        {q.no_kb_context && (
          <div className="mb-3 flex items-start gap-2.5 rounded-lg px-3.5 py-3 text-xs"
               style={{ background: 'rgba(239,68,68,0.07)', border: '1px solid rgba(239,68,68,0.25)', color: '#b91c1c' }}>
            <span className="mt-0.5 flex-shrink-0 text-sm">✕</span>
            <span>
              <span className="font-semibold">No knowledge base found.</span>
              {' '}There are no policy documents to draw from.{' '}
              <a href="/knowledge/upload" className="underline font-semibold hover:opacity-70">Upload your policies</a>
              {' '}to get suggested answers, or write this answer manually below.
            </span>
          </div>
        )}
        {q.confidence_reason && (
          <div className="mb-3 flex items-start gap-2.5 rounded-lg px-3.5 py-3 text-xs"
               style={{ background: 'rgba(239,68,68,0.07)', border: '1px solid rgba(239,68,68,0.2)', color: '#b91c1c' }}>
            <span className="mt-0.5 flex-shrink-0 text-sm">↓</span>
            <span>
              <span className="font-semibold">Low confidence — </span>{q.confidence_reason}
            </span>
          </div>
        )}
        {q.flag_note && (
          <div className="mb-3 flex items-start gap-2.5 rounded-lg px-3.5 py-3 text-xs"
               style={{ background: 'rgba(245,158,11,0.07)', border: '1px solid rgba(245,158,11,0.35)', color: '#92400e' }}>
            <span className="mt-0.5 flex-shrink-0 text-sm">⚑</span>
            <span>
              <span className="font-semibold">Flagged — </span>{q.flag_note}
            </span>
          </div>
        )}
        {q.conflict_warning && (
          <div className="mb-3 flex items-start gap-2.5 rounded-lg px-3.5 py-3 text-xs"
               style={{ background: 'rgba(245,158,11,0.08)', border: '1px solid rgba(245,158,11,0.35)', color: '#92400e' }}>
            <span className="mt-0.5 flex-shrink-0 text-sm">⚠</span>
            <span>
              <span className="font-semibold">Conflicts with a previously approved answer.</span>
              {' '}{q.conflict_warning}
            </span>
          </div>
        )}
        <label className="block text-xs font-semibold mb-2" style={{ color: t.text2 }}>Draft Answer</label>
        <textarea
          value={answer}
          onChange={e => handleChange(e.target.value)}
          rows={Math.max(4, Math.ceil(answer.length / 90))}
          className="w-full rounded-xl px-4 py-3 text-sm leading-relaxed resize-y outline-none transition-all"
          style={{ ...t.input, color: t.text, fontFamily: 'inherit' }}
          onFocus={e => e.target.style.boxShadow = `0 0 0 2px ${t.primary}40`}
          onBlur={e => e.target.style.boxShadow = 'none'}
        />

        <ReasoningPanel reasoning={q.reasoning} t={t} />
        <SourcesPanel citedChunks={q.cited_chunks} t={t} />
        <VersionHistoryPanel questionnaireId={questionnaireId} questionId={q.id} t={t} />
        <CommentsPanel
          questionnaireId={questionnaireId}
          questionId={q.id}
          currentUser={currentUser}
          t={t}
        />
      </div>

      {/* Action bar */}
      {canAct && (
        <div className="px-8 py-4 flex-shrink-0"
             style={{ borderTop: `1px solid ${t.borderColor}`,
                      background: t.dark ? 'rgba(255,255,255,0.02)' : t.surfaceHover }}>
          {/* Generic prompt — hidden in company mode (always generic) and when answer looks client-specific */}
          {!isCompany && customerName && detectIsGeneric(answer, customerName) && (
            <label className="flex items-center gap-2 mb-3 cursor-pointer w-fit group">
              <input
                type="checkbox"
                checked={makeGeneric}
                onChange={e => setMakeGeneric(e.target.checked)}
                className="w-3.5 h-3.5 rounded accent-indigo-500 cursor-pointer"
              />
              <span className="text-xs" style={{ color: t.text3 }}>
                Looks generic — save for{' '}
                <strong style={{ color: t.text2 }}>all clients</strong>
                , not just <span style={{ color: '#6366f1' }}>{customerName}</span>?
              </span>
            </label>
          )}
          <div className="flex items-center gap-3">
          <button onClick={() => { onApprove(q.id, isCompany || (detectIsGeneric(answer, customerName) && makeGeneric)); setMakeGeneric(isCompany) }}
                  className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold
                             text-white hover:opacity-90 active:scale-95 transition-all"
                  style={{ background: '#16a34a' }}>
            <Icon name="check" size={14} color="white" />
            Approve <kbd className="kbd ml-1">A</kbd>
          </button>
          <button onClick={() => onReject(q.id)}
                  className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold
                             hover:opacity-90 active:scale-95 transition-all"
                  style={{ background: t.dark ? 'rgba(239,68,68,0.1)' : '#fef2f2',
                           color: '#dc2626',
                           border: `1px solid ${t.dark ? 'rgba(239,68,68,0.25)' : 'rgba(239,68,68,0.3)'}` }}>
            <Icon name="x" size={14} color="#dc2626" />
            Reject <kbd className="kbd ml-1">X</kbd>
          </button>
          <button
            onClick={async () => { setRegening(true); await onRegen(q.id); setRegening(false) }}
            disabled={regening}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold
                       hover:opacity-90 active:scale-95 transition-all disabled:opacity-40"
            style={{ background: t.dark ? 'rgba(59,130,246,0.12)' : '#eff6ff',
                     color: t.primary,
                     border: `1px solid ${t.dark ? 'rgba(59,130,246,0.25)' : 'rgba(59,130,246,0.3)'}` }}>
            <span className={regening ? 'spin inline-block text-base leading-none' : ''}>↻</span>
            {regening ? 'Re-drafting…' : 'Re-draft'} {!regening && <kbd className="kbd ml-1">R</kbd>}
          </button>
          </div>
        </div>
      )}

      {(q.status === 'approved' || q.status === 'rejected') && (
        <div className="px-8 py-4 flex items-center gap-3 flex-shrink-0"
             style={{ borderTop: `1px solid ${t.borderColor}`,
                      background: q.status === 'approved'
                        ? (t.dark ? 'rgba(34,197,94,0.06)' : '#f0fdf4')
                        : (t.dark ? 'rgba(239,68,68,0.06)' : '#fef2f2') }}>
          <p className="text-sm font-semibold"
             style={{ color: q.status === 'approved' ? '#16a34a' : '#dc2626' }}>
            {q.status === 'approved' ? '✓ Approved — included in export' : '✗ Rejected — excluded from export'}
          </p>
          <button
            onClick={async () => { setRegening(true); await onRegen(q.id); setRegening(false) }}
            disabled={regening}
            className="ml-auto flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold
                       hover:opacity-80 transition-all disabled:opacity-40"
            style={{ background: t.dark ? 'rgba(59,130,246,0.12)' : '#eff6ff',
                     color: t.primary,
                     border: `1px solid ${t.dark ? 'rgba(59,130,246,0.2)' : 'rgba(59,130,246,0.3)'}` }}>
            <span className={regening ? 'spin inline-block' : ''}>↻</span>
            {regening ? 'Re-drafting…' : 'Re-draft'}
          </button>
        </div>
      )}
    </div>
  )
}

// ── Main page ─────────────────────────────────────────────────────────────
export default function QuestionnaireDetail() {
  const { id } = useParams()
  const nav = useNavigate()
  const { t } = useTheme()
  const { user: currentUser } = useAuth()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [genProgress, setGenProgress] = useState(0)
  const [currentId, setCurrentId] = useState(null)
  const [animMap, setAnimMap] = useState({})
  const [toast, setToast] = useState(null)
  const [shareLink, setShareLink] = useState(null)
  const [shareCopied, setShareCopied] = useState(false)
  const [reassigning, setReassigning] = useState(false)
  const [reassignValue, setReassignValue] = useState('')
  const [dueDateEditing, setDueDateEditing] = useState(false)
  const [dueDateValue, setDueDateValue] = useState('')
  const [savingDueDate, setSavingDueDate] = useState(false)
  const [clients, setClients] = useState([])
  const initializedRef = useRef(false)
  const emailVerified = currentUser?.email_verified !== false

  const load = useCallback(() => {
    setLoading(true)
    api.getQuestionnaire(id)
      .then(d => {
        setData(d)
        if (!initializedRef.current) {
          const first = d.questions.find(q => q.status === 'pending' || q.status === 'generated')
          if (first) { setCurrentId(first.id); initializedRef.current = true }
          else if (d.questions.length) { setCurrentId(d.questions[0].id); initializedRef.current = true }
        }
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [id])

  useEffect(load, [load])

  const qs        = data?.questionnaire
  const questions = data?.questions || []
  const toReview  = questions.filter(q => q.status === 'pending' || q.status === 'generated')
  const approved  = questions.filter(q => q.status === 'approved')
  const rejected  = questions.filter(q => q.status === 'rejected')
  const pct       = questions.length ? Math.round(((approved.length + rejected.length) / questions.length) * 100) : 0
  const current   = questions.find(q => q.id === currentId)

  const showToast = (msg, color) => setToast({ msg, color })

  const openReassign = () => {
    setReassignValue(qs?.customer_name || '')
    api.getClients().then(setClients).catch(() => {})
    setReassigning(true)
  }

  const submitReassign = async () => {
    try {
      const updated = await api.reassignQuestionnaire(id, reassignValue)
      setData(d => ({ ...d, questionnaire: updated }))
      setReassigning(false)
      showToast('Client updated', 'green')
    } catch {
      showToast('Failed to update client', 'red')
    }
  }

  const openDueDateEdit = () => {
    setDueDateValue(dueDateInputFromIso(qs?.due_date))
    setDueDateEditing(true)
  }

  const submitDueDate = async () => {
    setSavingDueDate(true)
    try {
      const iso = isoDueDateFromInput(dueDateValue)
      const updated = await api.updateDueDate(id, iso)
      setData(d => ({ ...d, questionnaire: updated }))
      setDueDateEditing(false)
      showToast(iso ? 'Due date saved' : 'Due date cleared', 'green')
    } catch {
      showToast('Failed to update due date', 'red')
    }
    setSavingDueDate(false)
  }

  const flash = (qId, cls) => {
    setAnimMap(p => ({ ...p, [qId]: cls }))
    setTimeout(() => setAnimMap(p => { const n = { ...p }; delete n[qId]; return n }), 600)
  }

  const advanceNext = useCallback(() => {
    const idx = toReview.findIndex(q => q.id === currentId)
    const next = toReview[idx + 1]
    if (next) setTimeout(() => setCurrentId(next.id), 260)
  }, [toReview, currentId])

  const handleApprove = useCallback(async (qId, makeGeneric = false) => {
    flash(qId, 'approve-flash')
    try {
      const updated = await api.approveQuestion(id, qId, makeGeneric)
      setData(p => ({ ...p, questions: p.questions.map(q => q.id === qId ? updated : q) }))
      showToast(makeGeneric ? 'Approved as generic answer' : 'Answer approved', 'green')
      advanceNext()
    } catch { showToast('Failed to approve', 'red') }
  }, [id, advanceNext])

  const handleReject = useCallback(async (qId) => {
    flash(qId, 'reject-flash')
    try {
      const updated = await api.rejectQuestion(id, qId)
      setData(p => ({ ...p, questions: p.questions.map(q => q.id === qId ? updated : q) }))
      showToast('Question flagged', 'red')
      advanceNext()
    } catch { showToast('Failed to flag', 'red') }
  }, [id, advanceNext])

  const pollGeneration = useCallback((startingPending) => {
    const pollIv = setInterval(async () => {
      try {
        const [st, fresh] = await Promise.all([
          api.getGenerationStatus(id),
          api.getQuestionnaire(id),
        ])
        setData(fresh)
        if (!initializedRef.current) {
          const first = fresh.questions.find(q => q.status === 'generated')
          if (first) { setCurrentId(first.id); initializedRef.current = true }
        }
        setGenProgress(st.progress_pct ?? 0)
        if (st.generation_status === 'complete') {
          clearInterval(pollIv)
          setGenerating(false)
          setGenProgress(100)
          showToast(`${st.generation_done_count ?? 0} answers drafted`, 'green')
          initializedRef.current = false
          setTimeout(() => setGenProgress(0), 800)
        } else if (st.generation_status === 'failed') {
          clearInterval(pollIv)
          setGenerating(false)
          showToast(st.generation_error || 'Generation failed', 'red')
        }
      } catch {}
    }, 3000)
    return pollIv
  }, [id, showToast])

  const handleGenerate = async () => {
    const startingPending = questions.filter(q => q.status === 'pending').length
    if (!startingPending) return
    setGenerating(true); setGenProgress(0)
    showToast(`Generating ${startingPending} answers — watch them appear live`, 'blue')

    let pollIv
    try {
      await api.generateAnswers(id)
      pollIv = pollGeneration(startingPending)
    } catch (e) {
      showToast(e.message || 'Generation failed', 'red')
      setGenerating(false)
    }
  }

  useEffect(() => {
    if (qs?.generation_status !== 'running' || generating) return undefined
    setGenerating(true)
    const pending = questions.filter(q => q.status === 'pending').length
    const iv = pollGeneration(pending || qs?.question_count || 1)
    return () => clearInterval(iv)
  }, [qs?.generation_status, id])

  const handleRegenerate = useCallback(async (qId) => {
    try {
      const updated = await api.regenerateQuestion(id, qId)
      setData(p => ({ ...p, questions: p.questions.map(q => q.id === qId ? updated : q) }))
      showToast('Answer updated', 'blue')
    } catch { showToast('Regeneration failed', 'red') }
  }, [id])

  const handleFlagged = useCallback((updated) => {
    setData(p => ({ ...p, questions: p.questions.map(q => q.id === updated.id ? updated : q) }))
  }, [])

  // Initialise share link if already generated
  useEffect(() => {
    if (qs?.share_token) setShareLink(`${window.location.origin}/share/${qs.share_token}`)
  }, [qs?.share_token])

  const handleShare = async () => {
    if (shareLink) {
      navigator.clipboard.writeText(shareLink)
      setShareCopied(true)
      setTimeout(() => setShareCopied(false), 2000)
      return
    }
    try {
      const res = await api.getShareToken(id)
      const link = `${window.location.origin}/share/${res.token}`
      setShareLink(link)
      navigator.clipboard.writeText(link)
      setShareCopied(true)
      setTimeout(() => setShareCopied(false), 2000)
    } catch { showToast('Failed to generate link', 'red') }
  }

  // Keyboard shortcuts
  useEffect(() => {
    const handler = e => {
      if (['INPUT', 'TEXTAREA'].includes(e.target.tagName)) return
      if (!currentId) return
      if (e.key === 'a' || e.key === 'A') handleApprove(currentId)
      if (e.key === 'x' || e.key === 'X') handleReject(currentId)
      if (e.key === 'r' || e.key === 'R') handleRegenerate(currentId)
      if (e.key === 'ArrowDown' || e.key === 'ArrowRight') {
        e.preventDefault()
        const idx = questions.findIndex(q => q.id === currentId)
        if (idx < questions.length - 1) setCurrentId(questions[idx + 1].id)
      }
      if (e.key === 'ArrowUp' || e.key === 'ArrowLeft') {
        e.preventDefault()
        const idx = questions.findIndex(q => q.id === currentId)
        if (idx > 0) setCurrentId(questions[idx - 1].id)
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [currentId, questions, toReview, handleApprove, handleReject])

  if (loading) return (
    <div className="h-full p-8 space-y-4" style={{ background: t.bg }}>
      <div className="skeleton h-8 rounded-lg w-48" />
      <div className="skeleton h-40 rounded-xl" />
    </div>
  )

  return (
    <div className="flex overflow-hidden h-full" style={{ background: t.bg }}>

      {/* ── Left panel: navigation ───────────────────────────────────── */}
      <aside className="w-[256px] shrink-0 flex flex-col overflow-hidden"
             style={{ background: t.sidebar, borderRight: `1px solid ${t.sidebarBorder}` }}>

        {/* Header */}
        <div className="px-4 pt-4 pb-4 flex-shrink-0"
             style={{ borderBottom: `1px solid ${t.borderColor}` }}>
          <button onClick={() => nav('/questionnaires')}
                  className="flex items-center gap-1.5 text-xs font-medium mb-3 transition-opacity hover:opacity-70"
                  style={{ color: t.text3 }}>
            <Icon name="arrowL" size={12} color={t.text3} /> Questionnaires
          </button>
          <p className="text-sm font-semibold leading-snug" style={{ color: t.text }}>
            {qs?.name}
          </p>
          {qs?.source_sheet_name && (
            <p className="text-[11px] mt-0.5" style={{ color: t.text3 }}>
              Worksheet: {qs.source_sheet_name}
            </p>
          )}
          <div className="flex flex-wrap items-center gap-1.5 mt-1">
            {qs?.status && <StatusBadge status={qs.status} />}
            <GenerationBadge status={qs?.generation_status} />
          </div>
          {qs?.customer_name && !reassigning && (
            <div className="flex items-center gap-1 mt-0.5 group">
              <p className="text-xs" style={{ color: t.text3 }}>{qs.customer_name}</p>
              {(currentUser?.role === 'owner' || currentUser?.role === 'admin') && currentUser?.workspace_type !== 'company' && (
                <button
                  onClick={openReassign}
                  className="opacity-0 group-hover:opacity-100 transition-opacity"
                  title="Change client"
                >
                  <Icon name="edit" size={11} color={t.text3} />
                </button>
              )}
            </div>
          )}
          {reassigning && (
            <div className="mt-1 flex flex-col gap-1">
              <input
                autoFocus
                list="reassign-clients"
                value={reassignValue}
                onChange={e => setReassignValue(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter') submitReassign(); if (e.key === 'Escape') setReassigning(false) }}
                className="text-xs rounded px-2 py-1 w-full"
                style={{ background: t.inputBg, color: t.text, border: `1px solid ${t.borderColor}` }}
                placeholder="Client name"
              />
              <datalist id="reassign-clients">
                {clients.map(c => <option key={c} value={c} />)}
              </datalist>
              <div className="flex gap-1">
                <button
                  onClick={submitReassign}
                  className="flex-1 text-xs rounded px-2 py-1 font-medium"
                  style={{ background: t.primary, color: '#fff' }}
                >Save</button>
                <button
                  onClick={() => setReassigning(false)}
                  className="text-xs rounded px-2 py-1"
                  style={{ background: t.dark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.08)', color: t.text2 }}
                >Cancel</button>
              </div>
            </div>
          )}

          {/* Due date */}
          <div className="mt-2 group">
            {dueDateEditing ? (
              <div className="flex flex-col gap-1">
                <label className="text-[10px] font-semibold uppercase tracking-wide" style={{ color: t.text3 }}>
                  Due date
                </label>
                <input
                  type="date"
                  autoFocus
                  value={dueDateValue}
                  onChange={e => setDueDateValue(e.target.value)}
                  onKeyDown={e => {
                    if (e.key === 'Enter') submitDueDate()
                    if (e.key === 'Escape') setDueDateEditing(false)
                  }}
                  className="text-xs rounded px-2 py-1 w-full"
                  style={{ background: t.inputBg, color: t.text, border: `1px solid ${t.borderColor}` }}
                />
                <div className="flex gap-1">
                  <button
                    onClick={submitDueDate}
                    disabled={savingDueDate}
                    className="flex-1 text-xs rounded px-2 py-1 font-medium disabled:opacity-50"
                    style={{ background: t.primary, color: '#fff' }}
                  >Save</button>
                  {qs?.due_date && (
                    <button
                      onClick={async () => {
                        setSavingDueDate(true)
                        try {
                          const updated = await api.updateDueDate(id, null)
                          setData(d => ({ ...d, questionnaire: updated }))
                          setDueDateEditing(false)
                          showToast('Due date cleared', 'green')
                        } catch {
                          showToast('Failed to clear due date', 'red')
                        }
                        setSavingDueDate(false)
                      }}
                      disabled={savingDueDate}
                      className="text-xs rounded px-2 py-1 disabled:opacity-50"
                      style={{ background: t.dark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.08)', color: t.text2 }}
                    >Clear</button>
                  )}
                  <button
                    onClick={() => setDueDateEditing(false)}
                    className="text-xs rounded px-2 py-1"
                    style={{ background: t.dark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.08)', color: t.text2 }}
                  >Cancel</button>
                </div>
              </div>
            ) : (
              <div className="flex items-center gap-1.5">
                <Icon name="clock" size={12} color={t.text3} />
                {qs?.due_date ? (
                  <span
                    className="text-xs font-medium"
                    style={{
                      color: dueDateUrgency(qs.due_date, qs.status) === 'overdue' ? '#ef4444'
                        : dueDateUrgency(qs.due_date, qs.status) === 'soon' ? '#f59e0b'
                        : t.text2,
                    }}
                  >
                    Due {formatDueDate(qs.due_date)}
                    {dueDateUrgency(qs.due_date, qs.status) === 'overdue' && ' · Overdue'}
                    {dueDateUrgency(qs.due_date, qs.status) === 'soon' && ' · Soon'}
                  </span>
                ) : (
                  <span className="text-xs" style={{ color: t.text3 }}>No due date</span>
                )}
                <button
                  onClick={openDueDateEdit}
                  className="opacity-0 group-hover:opacity-100 transition-opacity ml-auto"
                  title="Edit due date"
                >
                  <Icon name="edit" size={11} color={t.text3} />
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Progress */}
        <div className="px-4 py-4 flex-shrink-0"
             style={{ borderBottom: `1px solid ${t.borderColor}` }}>
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold" style={{ color: t.text2 }}>Progress</span>
            <span className="text-xs font-bold" style={{ color: t.text }}>{pct}%</span>
          </div>
          <div className="h-1.5 rounded-full overflow-hidden mb-3"
               style={{ background: t.dark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.08)' }}>
            <div className="h-full rounded-full transition-all duration-500"
                 style={{ width: `${pct}%`, background: t.primary }} />
          </div>
          {generating && (
            <div className="h-1 rounded-full overflow-hidden mb-3"
                 style={{ background: t.dark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)' }}>
              <div className="h-full rounded-full transition-all"
                   style={{ width: `${genProgress}%`, background: '#f59e0b' }} />
            </div>
          )}
          <div className="grid grid-cols-3 gap-2 text-center">
            {[
              { label: 'Review', val: toReview.length, color: '#f59e0b' },
              { label: 'Approved', val: approved.length, color: '#22c55e' },
              { label: 'Flagged', val: rejected.length, color: '#ef4444' },
            ].map(s => (
              <div key={s.label} className="rounded-lg py-2"
                   style={{ background: t.dark ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.04)' }}>
                <p className="text-base font-bold" style={{ color: s.color }}>{s.val}</p>
                <p className="text-[10px]" style={{ color: t.text3 }}>{s.label}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Question list */}
        <div className="flex-1 overflow-y-auto px-2 py-2">
          {questions.map((q, i) => {
            const isActive = q.id === currentId
            const noKb = q.no_kb_context
            const hasConflict = !!q.conflict_warning
            const isFlagged = !!q.flag_note
            const dot = q.status === 'approved' ? '#22c55e'
                      : q.status === 'rejected'  ? '#ef4444'
                      : noKb                      ? '#ef4444'
                      : hasConflict               ? '#d97706'
                      : isFlagged                 ? '#d97706'
                      : q.status === 'generated' ? t.primary
                      : t.text3
            return (
              <button key={q.id} onClick={() => setCurrentId(q.id)}
                      className="w-full text-left px-3 py-2.5 rounded-lg mb-0.5 transition-all"
                      style={{
                        background: isActive
                          ? (t.dark ? 'rgba(59,130,246,0.12)' : 'rgba(37,99,235,0.08)')
                          : isFlagged ? 'rgba(245,158,11,0.05)' : 'transparent',
                        border: `1px solid ${isActive ? `${t.primary}40` : isFlagged ? 'rgba(245,158,11,0.25)' : 'transparent'}`,
                      }}
                      onMouseEnter={e => { if (!isActive) e.currentTarget.style.background = t.dark ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.04)' }}
                      onMouseLeave={e => { if (!isActive) e.currentTarget.style.background = isFlagged ? 'rgba(245,158,11,0.05)' : 'transparent' }}>
                <div className="flex items-center gap-2">
                  <div className="w-1.5 h-1.5 rounded-full flex-shrink-0" style={{ background: dot }} />
                  <span className="text-xs font-semibold" style={{ color: isActive ? t.primary : t.text }}>
                    Q{i + 1}
                  </span>
                  {noKb ? (
                    <span className="ml-auto text-[9px] font-bold px-1.5 py-0.5 rounded"
                          style={{ background: 'rgba(239,68,68,0.1)', color: '#b91c1c', border: '1px solid rgba(239,68,68,0.25)' }}>
                      MANUAL
                    </span>
                  ) : hasConflict ? (
                    <span className="ml-auto text-[9px] font-bold px-1.5 py-0.5 rounded"
                          style={{ background: 'rgba(245,158,11,0.1)', color: '#b45309', border: '1px solid rgba(245,158,11,0.3)' }}>
                      CONFLICT
                    </span>
                  ) : isFlagged ? (
                    <span className="ml-auto" style={{ color: '#d97706', fontSize: 11 }} title={q.flag_note}>⚑</span>
                  ) : q.confidence === 'high' && q.status === 'generated' && (
                    <span className="ml-auto text-[10px] font-semibold" style={{ color: '#22c55e' }}>H</span>
                  )}
                </div>
                <p className="text-[11px] mt-0.5 leading-snug line-clamp-2"
                   style={{ color: t.text2 }}>
                  {q.question_text.substring(0, 60)}{q.question_text.length > 60 ? '…' : ''}
                </p>
              </button>
            )
          })}
        </div>

        {/* Actions */}
        <div className="px-3 py-3 space-y-2 flex-shrink-0"
             style={{ borderTop: `1px solid ${t.borderColor}` }}>
          {qs?.generation_status === 'failed' && qs.generation_error && (
            <div className="px-3 py-2 rounded-lg text-[11px] leading-snug"
                 style={{ background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.25)', color: '#b91c1c' }}>
              Generation failed: {qs.generation_error}
            </div>
          )}
          {!emailVerified && (
            <p className="text-[11px] px-1" style={{ color: '#92400e' }}>
              Verify your email to generate answers.
            </p>
          )}
          <button
            onClick={handleGenerate}
            disabled={generating || qs?.generation_status === 'running'}
            title={!emailVerified ? 'Verify your email to generate (required in production)' : undefined}
            className="w-full flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-semibold
                             text-white hover:opacity-90 disabled:opacity-50 transition-all"
            style={{ background: t.primary }}
          >
            {generating || qs?.generation_status === 'running'
              ? <><span className="spin inline-block">↻</span> {genProgress < 90 ? `${genProgress}%` : 'Finishing…'}</>
              : <><Icon name="spark" size={13} color="white" /> Draft Answers</>}
          </button>
          {(() => {
            const allDone = toReview.length === 0 && questions.length > 0
            const exportStyle = allDone
              ? { background: '#16a34a', color: 'white' }
              : { background: t.dark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)',
                  color: t.text2, border: `1px solid ${t.borderColor}` }
            const exportLabel = allDone
              ? 'Export & Send'
              : approved.length > 0
                ? `Export (${approved.length}/${questions.length} approved)`
                : 'Export XLSX'
            return (
              <a href={api.exportUrl(id)} download
                 className="w-full flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-semibold
                            hover:opacity-80 transition-all no-underline"
                 style={exportStyle}>
                <Icon name="download" size={13} color={allDone ? 'white' : t.text2} />
                {exportLabel}
              </a>
            )
          })()}
        </div>
      </aside>

      {/* ── Right panel: question detail ─────────────────────────────── */}
      <div className="flex-1 overflow-hidden flex flex-col" style={{ background: t.surface }}>

        {/* Top bar */}
        <div className="px-8 py-3.5 flex items-center justify-between flex-shrink-0"
             style={{ borderBottom: `1px solid ${t.borderColor}` }}>
          <div className="flex items-center gap-3">
            <span className="text-sm font-semibold" style={{ color: t.text2 }}>
              {current ? `Question ${questions.indexOf(current) + 1} of ${questions.length}` : 'Select a question'}
            </span>
            {qs?.status && <StatusBadge status={qs.status} />}
          </div>
            <div className="flex items-center gap-1">
            <button
              onClick={() => {
                const idx = questions.findIndex(q => q.id === currentId)
                if (idx > 0) setCurrentId(questions[idx - 1].id)
              }}
              disabled={!currentId || questions.findIndex(q => q.id === currentId) === 0}
              className="w-8 h-8 rounded-lg flex items-center justify-center transition-all disabled:opacity-30 hover:opacity-70"
              style={{ background: t.dark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)', color: t.text2 }}
              title="Previous question (↑)">
              <svg width={14} height={14} viewBox="0 0 24 24" fill="none" stroke={t.text2} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="m4.5 15.75 7.5-7.5 7.5 7.5"/>
              </svg>
            </button>
            <button
              onClick={() => {
                const idx = questions.findIndex(q => q.id === currentId)
                if (idx < questions.length - 1) setCurrentId(questions[idx + 1].id)
              }}
              disabled={!currentId || questions.findIndex(q => q.id === currentId) === questions.length - 1}
              className="w-8 h-8 rounded-lg flex items-center justify-center transition-all disabled:opacity-30 hover:opacity-70"
              style={{ background: t.dark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)', color: t.text2 }}
              title="Next question (↓)">
              <svg width={14} height={14} viewBox="0 0 24 24" fill="none" stroke={t.text2} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="m19.5 8.25-7.5 7.5-7.5-7.5"/>
              </svg>
            </button>
            <span className="text-xs ml-2" style={{ color: t.text3 }}>
              <kbd className="kbd">A</kbd> approve · <kbd className="kbd">X</kbd> reject · <kbd className="kbd">R</kbd> regen
            </span>
            <button
              onClick={handleShare}
              className="ml-3 flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all hover:opacity-80"
              style={{ background: t.dark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)',
                       color: t.text2, border: `1px solid ${t.borderColor}` }}
              title="Copy a read-only progress link to share with stakeholders">
              {shareCopied ? '✓ Copied' : shareLink ? 'Copy progress link' : 'Share progress'}
            </button>
          </div>
        </div>

        {/* Question detail */}
        {current ? (
          <div className="flex-1 overflow-hidden">
            <QuestionDetail
              key={current.id}
              q={current}
              qIdx={questions.indexOf(current)}
              questionnaireId={id}
              customerName={qs?.customer_name}
              onApprove={handleApprove}
              onReject={handleReject}
              onRegen={handleRegenerate}
              onFlagged={handleFlagged}
              animClass={animMap[current.id]}
              t={t}
            />
          </div>
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center max-w-xs">
              {toReview.length === 0 && questions.length > 0 ? (
                <>
                  <div className="w-14 h-14 rounded-full mx-auto mb-4 flex items-center justify-center"
                       style={{ background: 'rgba(22,163,74,0.1)', border: '1px solid rgba(22,163,74,0.25)' }}>
                    <Icon name="check" size={26} color="#16a34a" />
                  </div>
                  <p className="text-base font-bold mb-1" style={{ color: t.text }}>Ready to send!</p>
                  <p className="text-sm mb-1.5" style={{ color: t.text2 }}>
                    {approved.length} answer{approved.length !== 1 ? 's' : ''} approved
                    {rejected.length > 0 && <span style={{ color: t.text3 }}> · {rejected.length} flagged (excluded)</span>}
                  </p>
                  <p className="text-xs mb-5" style={{ color: t.text3 }}>
                    Your filled spreadsheet is ready to email back to the customer.
                  </p>
                  <a href={api.exportUrl(id)} download
                     className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold text-white hover:opacity-90 no-underline"
                     style={{ background: '#16a34a' }}>
                    <Icon name="download" size={14} color="white" /> Download & Send
                  </a>
                </>
              ) : (
                <p className="text-sm font-medium" style={{ color: t.text3 }}>
                  Click Draft Answers to begin
                </p>
              )}
            </div>
          </div>
        )}
      </div>

      {toast && <Toast msg={toast.msg} color={toast.color} onDone={() => setToast(null)} />}
    </div>
  )
}
