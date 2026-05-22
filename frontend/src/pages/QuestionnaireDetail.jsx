import { useState, useEffect, useRef, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api } from '../api'
import { useTheme } from '../context/ThemeContext'
import { useAuth } from '../context/AuthContext'
import { Icon } from '../components/Layout'
import { StatusBadge, ConfidenceBadge } from '../components/StatusBadge'

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
          const uploadedAt = c?.document_uploaded_at ? new Date(c.document_uploaded_at) : null
          const monthsOld = uploadedAt ? Math.floor((Date.now() - uploadedAt) / (1000 * 60 * 60 * 24 * 30)) : null
          const isStale = monthsOld !== null && monthsOld >= 12
          const dateLabel = uploadedAt
            ? uploadedAt.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
            : null
          return (
            <div key={id} className="rounded-lg p-3"
                 style={{ background: t.dark ? 'rgba(59,130,246,0.05)' : '#eff6ff',
                          border: `1px solid ${isStale ? 'rgba(245,158,11,0.4)' : (t.dark ? 'rgba(59,130,246,0.15)' : 'rgba(59,130,246,0.2)')}` }}>
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
                          style={{ color: isStale ? '#b45309' : t.text3 }}
                          title={isStale ? `Uploaded ${monthsOld} months ago — verify this policy is still current` : `Uploaded ${dateLabel}`}>
                      {isStale && '⚠ '}Uploaded {dateLabel}
                    </span>
                  )}
                  <ScoreBadge score={score} />
                </div>
              </div>
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

// ── Assign dropdown ────────────────────────────────────────────────────────
function AssignDropdown({ q, questionnaireId, teamMembers, currentUser, onAssigned, t }) {
  const [open, setOpen] = useState(false)
  const [assigning, setAssigning] = useState(false)
  const canAssign = currentUser?.role === 'owner' || currentUser?.role === 'admin'
  const ref = useRef(null)

  useEffect(() => {
    const handler = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false) }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const assign = async (userId) => {
    setAssigning(true)
    setOpen(false)
    try {
      const updated = await api.assignQuestion(questionnaireId, q.id, userId)
      onAssigned(updated)
    } catch {}
    setAssigning(false)
  }

  const assigneeName = q.assigned_to_name || q.assigned_to_email

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => canAssign && setOpen(o => !o)}
        disabled={assigning}
        className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium transition-all"
        style={{
          background: assigneeName
            ? (t.dark ? 'rgba(59,130,246,0.1)' : '#eff6ff')
            : (t.dark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)'),
          color: assigneeName ? t.primary : t.text3,
          border: `1px solid ${assigneeName ? `${t.primary}40` : t.borderColor}`,
          cursor: canAssign ? 'pointer' : 'default',
        }}>
        <Icon name="user" size={11} color={assigneeName ? t.primary : t.text3} />
        {assigning ? 'Assigning…' : (assigneeName || 'Unassigned')}
        {canAssign && <span style={{ color: t.text3, fontSize: 9 }}>▾</span>}
      </button>
      {open && canAssign && (
        <div className="absolute left-0 top-full mt-1 z-50 rounded-xl overflow-hidden shadow-2xl min-w-[180px]"
             style={{ background: t.surface, border: `1px solid ${t.borderColor}` }}>
          <button
            onClick={() => assign(null)}
            className="w-full text-left px-3 py-2 text-xs transition-colors"
            style={{ color: t.text3 }}
            onMouseEnter={e => e.currentTarget.style.background = t.dark ? 'rgba(255,255,255,0.06)' : '#f3f4f6'}
            onMouseLeave={e => e.currentTarget.style.background = 'transparent'}>
            Unassign
          </button>
          {teamMembers.map(m => (
            <button
              key={m.id}
              onClick={() => assign(m.id)}
              className="w-full text-left px-3 py-2 text-xs transition-colors"
              style={{ color: q.assigned_to_id === m.id ? t.primary : t.text,
                       background: q.assigned_to_id === m.id
                         ? (t.dark ? 'rgba(59,130,246,0.1)' : '#eff6ff')
                         : 'transparent' }}
              onMouseEnter={e => { if (q.assigned_to_id !== m.id) e.currentTarget.style.background = t.dark ? 'rgba(255,255,255,0.06)' : '#f3f4f6' }}
              onMouseLeave={e => { if (q.assigned_to_id !== m.id) e.currentTarget.style.background = 'transparent' }}>
              <span className="font-semibold">{m.full_name || m.email}</span>
              <span className="ml-1" style={{ color: t.text3 }}>· {m.role}</span>
            </button>
          ))}
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
function QuestionDetail({ q, qIdx, questionnaireId, teamMembers, currentUser, onApprove, onReject, onRegen, onAssigned, animClass, t }) {
  const [answer, setAnswer] = useState(q.draft_answer || '')
  const [saving, setSaving] = useState(false)
  const [regening, setRegening] = useState(false)
  const saveTimer = useRef(null)

  useEffect(() => setAnswer(q.draft_answer || ''), [q.id, q.draft_answer])

  const handleChange = (val) => {
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
            <AssignDropdown
              q={q}
              questionnaireId={questionnaireId}
              teamMembers={teamMembers}
              currentUser={currentUser}
              onAssigned={onAssigned}
              t={t}
            />
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
              {' '}to enable automated drafting, or write this answer manually below.
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
        {q.has_starter_sources && (
          <div className="mb-3 flex items-start gap-2.5 rounded-lg px-3.5 py-3 text-xs"
               style={{ background: 'rgba(245,158,11,0.08)', border: '1px solid rgba(245,158,11,0.3)', color: '#92400e' }}>
            <span className="mt-0.5 flex-shrink-0 text-sm">⚠</span>
            <span>
              <span className="font-semibold">Based on starter templates, not your real policies.</span>
              {' '}Verify this answer before approving, or{' '}
              <a href="/knowledge/upload" className="underline font-semibold hover:opacity-70">upload your own policies</a>
              {' '}to get accurate, company-specific answers.
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
        <div className="px-8 py-4 flex items-center gap-3 flex-shrink-0"
             style={{ borderTop: `1px solid ${t.borderColor}`,
                      background: t.dark ? 'rgba(255,255,255,0.02)' : t.surfaceHover }}>
          <button onClick={() => onApprove(q.id)}
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
  const [teamMembers, setTeamMembers] = useState([])
  const [shareLink, setShareLink] = useState(null)
  const [shareCopied, setShareCopied] = useState(false)
  const initializedRef = useRef(false)

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

  // Fetch team members once so assignment dropdown is populated
  useEffect(() => {
    api.getTeam().then(setTeamMembers).catch(() => {})
  }, [])

  const qs        = data?.questionnaire
  const questions = data?.questions || []
  const toReview  = questions.filter(q => q.status === 'pending' || q.status === 'generated')
  const approved  = questions.filter(q => q.status === 'approved')
  const rejected  = questions.filter(q => q.status === 'rejected')
  const highConf  = questions.filter(q => q.status === 'generated' && q.confidence === 'high')
  const pct       = questions.length ? Math.round(((approved.length + rejected.length) / questions.length) * 100) : 0
  const current   = questions.find(q => q.id === currentId)

  const showToast = (msg, color) => setToast({ msg, color })

  const flash = (qId, cls) => {
    setAnimMap(p => ({ ...p, [qId]: cls }))
    setTimeout(() => setAnimMap(p => { const n = { ...p }; delete n[qId]; return n }), 600)
  }

  const advanceNext = useCallback(() => {
    const idx = toReview.findIndex(q => q.id === currentId)
    const next = toReview[idx + 1]
    if (next) setTimeout(() => setCurrentId(next.id), 260)
  }, [toReview, currentId])

  const handleApprove = useCallback(async (qId) => {
    flash(qId, 'approve-flash')
    try {
      const updated = await api.approveQuestion(id, qId)
      setData(p => ({ ...p, questions: p.questions.map(q => q.id === qId ? updated : q) }))
      showToast('Answer approved', 'green')
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

  const handleGenerate = async () => {
    const startingPending = questions.filter(q => q.status === 'pending').length
    if (!startingPending) return
    setGenerating(true); setGenProgress(0)
    showToast(`Generating ${startingPending} answers — watch them appear live`, 'blue')

    // Poll every 3s so questions appear as they complete on the backend
    const pollIv = setInterval(async () => {
      try {
        const fresh = await api.getQuestionnaire(id)
        setData(fresh)
        // Auto-focus first newly-generated question if nothing is selected yet
        if (!initializedRef.current) {
          const first = fresh.questions.find(q => q.status === 'generated')
          if (first) { setCurrentId(first.id); initializedRef.current = true }
        }
        // Real progress: how many pending→generated so far
        const nowPending = fresh.questions.filter(q => q.status === 'pending').length
        const done = startingPending - nowPending
        setGenProgress(Math.min(Math.round((done / startingPending) * 100), 95))
      } catch {}
    }, 3000)

    try {
      const res = await api.generateAnswers(id)
      clearInterval(pollIv)
      // Final reload to catch the last question
      const final = await api.getQuestionnaire(id)
      setData(final)
      setGenProgress(100)
      showToast(`${res.updated} answers drafted`, 'green')
      initializedRef.current = false
    } catch {
      showToast('Generation failed', 'red')
    }
    clearInterval(pollIv)
    setGenerating(false)
    setTimeout(() => setGenProgress(0), 800)
  }

  const handleRegenerate = useCallback(async (qId) => {
    try {
      const updated = await api.regenerateQuestion(id, qId)
      setData(p => ({ ...p, questions: p.questions.map(q => q.id === qId ? updated : q) }))
      showToast('Answer updated', 'blue')
    } catch { showToast('Regeneration failed', 'red') }
  }, [id])

  const handleAssigned = useCallback((updated) => {
    setData(p => ({ ...p, questions: p.questions.map(q => q.id === updated.id ? updated : q) }))
  }, [])

  const handleBulkApprove = async () => {
    if (!highConf.length || !confirm(`Approve all ${highConf.length} high-confidence answers?`)) return
    try {
      const res = await api.bulkApproveHigh(id)
      await load()
      showToast(`Approved ${res.approved} answers`, 'green')
    } catch { showToast('Bulk approve failed', 'red') }
  }

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
    <div className="flex overflow-hidden" style={{ height: '100vh', background: t.bg }}>

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
          {qs?.customer_name && (
            <p className="text-xs mt-0.5" style={{ color: t.text3 }}>{qs.customer_name}</p>
          )}
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
            const dot = q.status === 'approved' ? '#22c55e'
                      : q.status === 'rejected'  ? '#ef4444'
                      : noKb                      ? '#ef4444'
                      : hasConflict               ? '#d97706'
                      : q.status === 'generated' ? t.primary
                      : t.text3
            return (
              <button key={q.id} onClick={() => setCurrentId(q.id)}
                      className="w-full text-left px-3 py-2.5 rounded-lg mb-0.5 transition-all"
                      style={{
                        background: isActive
                          ? (t.dark ? 'rgba(59,130,246,0.12)' : 'rgba(37,99,235,0.08)')
                          : 'transparent',
                        border: `1px solid ${isActive ? `${t.primary}40` : 'transparent'}`,
                      }}
                      onMouseEnter={e => { if (!isActive) e.currentTarget.style.background = t.dark ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.04)' }}
                      onMouseLeave={e => { if (!isActive) e.currentTarget.style.background = 'transparent' }}>
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
                  ) : q.confidence === 'high' && q.status === 'generated' && (
                    <span className="ml-auto text-[10px] font-semibold" style={{ color: '#22c55e' }}>H</span>
                  )}
                </div>
                <p className="text-[11px] mt-0.5 leading-snug line-clamp-2"
                   style={{ color: isActive ? t.text2 : t.text2 }}>
                  {q.question_text.substring(0, 60)}{q.question_text.length > 60 ? '…' : ''}
                </p>
              </button>
            )
          })}
        </div>

        {/* Actions */}
        <div className="px-3 py-3 space-y-2 flex-shrink-0"
             style={{ borderTop: `1px solid ${t.borderColor}` }}>
          {highConf.length > 0 && (
            <button onClick={handleBulkApprove}
                    className="w-full flex items-center justify-center gap-2 py-2 rounded-lg text-xs font-semibold transition-all hover:opacity-80"
                    style={{ background: t.dark ? 'rgba(34,197,94,0.1)' : '#f0fdf4',
                             color: '#16a34a',
                             border: '1px solid rgba(34,197,94,0.25)' }}>
              <Icon name="check" size={12} color="#16a34a" />
              Approve {highConf.length} high-conf
            </button>
          )}
          <button onClick={handleGenerate} disabled={generating}
                  className="w-full flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-semibold
                             text-white hover:opacity-90 disabled:opacity-50 transition-all"
                  style={{ background: t.primary }}>
            {generating
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
              teamMembers={teamMembers}
              currentUser={currentUser}
              onApprove={handleApprove}
              onReject={handleReject}
              onRegen={handleRegenerate}
              onAssigned={handleAssigned}
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
