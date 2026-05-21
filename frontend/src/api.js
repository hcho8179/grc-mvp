/** Thin wrapper around all FastAPI /api/* JSON endpoints.
 *  Auth is handled via HttpOnly cookie — no token in JS. */

const BASE = '/api'
const OPTS = { credentials: 'include' }  // send cookie on every request

async function get(path) {
  const res = await fetch(`${BASE}${path}`, OPTS)
  if (res.status === 401) { window.location.href = '/login'; throw new Error('Unauthorized') }
  if (!res.ok) throw new Error(`GET ${path} → ${res.status}`)
  return res.json()
}

async function post(path, body) {
  const res = await fetch(`${BASE}${path}`, {
    ...OPTS,
    method: 'POST',
    headers: body ? { 'Content-Type': 'application/json' } : {},
    body: body ? JSON.stringify(body) : undefined,
  })
  if (res.status === 401) { window.location.href = '/login'; throw new Error('Unauthorized') }
  if (!res.ok) throw new Error(`POST ${path} → ${res.status}`)
  return res.json()
}

async function patch(path, formData) {
  const res = await fetch(`${BASE}${path}`, {
    ...OPTS,
    method: 'PATCH',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams(formData),
  })
  if (res.status === 401) { window.location.href = '/login'; throw new Error('Unauthorized') }
  if (!res.ok) throw new Error(`PATCH ${path} → ${res.status}`)
  return res.json()
}

async function postFormRaw(path, formData) {
  const res = await fetch(`${BASE}${path}`, {
    ...OPTS,
    method: 'POST',
    body: formData,
  })
  const json = await res.json()
  if (res.status === 401) { window.location.href = '/login'; throw new Error('Unauthorized') }
  if (!res.ok) throw new Error(json.error || `POST ${path} → ${res.status}`)
  return json
}

export const api = {
  // Dashboard
  getDashboard: () => get('/dashboard'),

  // Questionnaires
  getQuestionnaires:    (page = 1)      => get(`/questionnaires?page=${page}&per_page=20`),
  getQuestionnaire:     (id)            => get(`/questionnaires/${id}`),
  generateAnswers:      (id)            => post(`/questionnaires/${id}/generate`),
  approveQuestion:      (qId, qId2)     => post(`/questionnaires/${qId}/questions/${qId2}/approve`),
  rejectQuestion:       (qId, qId2)     => post(`/questionnaires/${qId}/questions/${qId2}/reject`),
  regenerateQuestion:   (qId, qId2)     => post(`/questionnaires/${qId}/questions/${qId2}/regenerate`),
  bulkApproveHigh:      (id)            => post(`/questionnaires/${id}/bulk-approve-high`),
  updateQuestion:       (qId, qId2, answer) =>
    patch(`/questionnaires/${qId}/questions/${qId2}`, { draft_answer: answer }),
  deleteQuestionnaire:  (id)            => post(`/questionnaires/${id}/delete`),

  // Upload wizard
  uploadQuestionnairePrev:     (formData)         => postFormRaw('/questionnaires/upload/preview', formData),
  uploadQuestionnaireFinalize: (tempId, formData) => postFormRaw(`/questionnaires/upload/${tempId}/finalize`, formData),

  // Export
  exportUrl: (id) => `/api/questionnaires/${id}/export`,

  // Chunks
  getChunk: (chunkId) => get(`/chunks/${chunkId}`),

  // Knowledge base
  getKnowledge:    (page = 1) => get(`/knowledge?page=${page}&per_page=20`),
  deleteKnowledge: (id)       => post(`/knowledge/${id}/delete`),
  uploadKnowledge: (formData) => postFormRaw('/knowledge/upload', formData),

  // Answer library
  getAnswerLibrary: (q = '', category = '') =>
    get(`/answers/library?q=${encodeURIComponent(q)}&category=${encodeURIComponent(category)}`),

  // Templates
  getTemplates:    ()    => get('/templates'),
  deleteTemplate:  (id)  => post(`/templates/${id}/delete`),

  // Usage
  getUsage: () => get('/usage'),

  // Audit log
  getAuditLog: (action = '') =>
    get(`/audit${action ? `?action=${encodeURIComponent(action)}` : ''}`),

  // Assignment
  assignQuestion: (qsId, qId, userId) =>
    post(`/questionnaires/${qsId}/questions/${qId}/assign`, { user_id: userId }),

  // Comments
  getComments:   (qsId, qId)        => get(`/questionnaires/${qsId}/questions/${qId}/comments`),
  postComment:   (qsId, qId, body)  => post(`/questionnaires/${qsId}/questions/${qId}/comments`, { body }),
  deleteComment: (qsId, qId, cId)   =>
    fetch(`/api/questionnaires/${qsId}/questions/${qId}/comments/${cId}`, { ...OPTS, method: 'DELETE' }).then(r => r.json()),

  // My Assignments
  getMyAssignments: () => get('/assignments'),

  // KB Health
  getKBHealth: () => get('/kb-health'),

  // Team
  getTeam: () => get('/auth/team'),
  changeRole: (userId, role) =>
    fetch('/api/auth/team/' + userId + '/role', {
      ...OPTS,
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ role }),
    }).then(r => r.json()),

  // Email verification
  verifyEmail:         (token) => post('/auth/verify-email', { token }),
  resendVerification:  ()      => post('/auth/resend-verification', {}),

  // Trash & restore
  getTrash:              ()      => get('/trash'),
  restoreQuestionnaire:  (id)    => post(`/questionnaires/${id}/restore`, {}),
  restoreDocument:       (id)    => post(`/knowledge/${id}/restore`, {}),
}
