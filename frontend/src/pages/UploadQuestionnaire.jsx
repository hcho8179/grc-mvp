import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'
import { useTheme } from '../context/ThemeContext'
import { useAuth } from '../context/AuthContext'
import { Icon } from '../components/Layout'

export default function UploadQuestionnaire() {
  const { t } = useTheme()
  const { user } = useAuth()
  const isCompany = user?.workspace_type === 'company'
  const nav = useNavigate()
  const fileRef = useRef()
  const [step, setStep] = useState(1)
  const [file, setFile] = useState(null)
  const [name, setName] = useState('')
  const [customer, setCustomer] = useState('')
  const [dragging, setDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [finalizing, setFinalizing] = useState(false)
  const [error, setError] = useState('')
  const [preview, setPreview] = useState(null)
  const [questionCol, setQuestionCol] = useState(null)
  const [answerCol, setAnswerCol] = useState(null)
  const [evidenceCol, setEvidenceCol] = useState(null)
  const [result, setResult] = useState(null)
  const [clients, setClients] = useState([])

  useEffect(() => {
    if (!isCompany) api.getClients().then(setClients).catch(() => {})
  }, [])

  const handleFile = (f) => {
    if (!f) return
    const ext = f.name.toLowerCase().split('.').pop()
    if (!['xlsx', 'docx', 'pdf'].includes(ext)) { setError('Only XLSX, DOCX, and PDF files are supported.'); return }
    setError(''); setFile(f)
    if (!name) setName(f.name.replace(/\.(xlsx|docx|pdf)$/i, '').replace(/[_-]/g, ' ').trim())
  }

  const handleStep1 = async (e) => {
    e.preventDefault()
    if (!file) { setError('Please select a file.'); return }
    if (!name.trim()) { setError('Please enter a questionnaire name.'); return }
    setError(''); setUploading(true)
    try {
      const fd = new FormData()
      fd.append('file', file); fd.append('name', name.trim()); fd.append('customer_name', isCompany ? '' : customer.trim())
      const data = await api.uploadQuestionnairePrev(fd)
      setPreview(data)
      if (data.suggested_template) {
        setQuestionCol(data.suggested_template.question_col)
        setAnswerCol(data.suggested_template.answer_col ?? null)
      }
      setStep(2)
    } catch (e) { setError(e.message || 'Upload failed.') }
    setUploading(false)
  }

  const handleStep2 = async (e) => {
    e.preventDefault()
    if (!isDocOrPdf && questionCol === null) { setError('Please select the question column.'); return }
    setError(''); setFinalizing(true)
    try {
      const fd = new FormData()
      fd.append('question_col', isDocOrPdf ? 0 : questionCol)
      if (answerCol !== null) fd.append('answer_col', answerCol)
      if (evidenceCol !== null) fd.append('evidence_col', evidenceCol)
      const data = await api.uploadQuestionnaireFinalize(preview.temp_id, fd)
      setResult(data); setStep(3)
      setTimeout(() => nav(`/questionnaires/${data.id}`), 2200)
    } catch (e) { setError(e.message || 'Failed to create questionnaire.') }
    setFinalizing(false)
  }

  const inputStyle = { ...t.input, color: t.text }
  const inputCls = 'w-full px-3.5 py-2.5 rounded-xl text-sm outline-none transition-all'

  const isDocOrPdf = preview?.file_type !== 'xlsx' && preview != null
  const STEPS = ['Select File', isDocOrPdf ? 'Review Questions' : 'Pick Columns', 'Done']

  return (
    <div className="h-full overflow-y-auto">
      <div className="p-8 max-w-3xl mx-auto">

        <button onClick={() => step > 1 ? setStep(s => s - 1) : nav('/questionnaires')}
                className="flex items-center gap-1.5 text-xs font-medium mb-6 transition-opacity hover:opacity-70"
                style={{ color: t.text3 }}>
          <Icon name="arrowL" size={12} color={t.text3} />
          {step > 1 ? 'Back' : 'All Questionnaires'}
        </button>

        <h1 className="text-2xl font-bold mb-1" style={{ color: t.text }}>Upload Questionnaire</h1>
        <p className="text-sm mb-8" style={{ color: t.text2 }}>
          Upload an XLSX, DOCX, or PDF file and get draft answers for every question.
        </p>

        {/* Step indicator */}
        <div className="flex items-center gap-2 mb-8">
          {STEPS.map((label, i) => {
            const n = i + 1; const active = step === n; const done = step > n
            return (
              <div key={n} className="flex items-center gap-2">
                <div className="flex items-center gap-2">
                  <div className="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold transition-all"
                       style={done ? { background: '#22c55e', color: 'white' }
                                   : active ? { background: t.primary, color: 'white' }
                                   : { background: t.dark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.08)', color: t.text3 }}>
                    {done ? '✓' : n}
                  </div>
                  <span className="text-xs font-medium"
                        style={{ color: active ? t.text : done ? '#22c55e' : t.text3 }}>
                    {label}
                  </span>
                </div>
                {i < 2 && <div className="w-8 h-px mx-1" style={{ background: t.borderColor }} />}
              </div>
            )
          })}
        </div>

        {error && (
          <div className="mb-5 px-4 py-3 rounded-xl text-sm font-medium"
               style={{ background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)', color: '#ef4444' }}>
            {error}
          </div>
        )}

        {/* Step 1 */}
        {step === 1 && (
          <form onSubmit={handleStep1} className="space-y-4">
            <div className="rounded-xl border-2 border-dashed transition-all cursor-pointer flex flex-col items-center justify-center py-14 text-center"
                 style={{
                   borderColor: dragging ? t.primary : file ? '#22c55e' : t.borderColor,
                   background: dragging ? `${t.primary}08` : file ? 'rgba(34,197,94,0.04)' : t.dark ? 'rgba(255,255,255,0.02)' : 'rgba(0,0,0,0.02)',
                 }}
                 onClick={() => fileRef.current?.click()}
                 onDragOver={e => { e.preventDefault(); setDragging(true) }}
                 onDragLeave={() => setDragging(false)}
                 onDrop={e => { e.preventDefault(); setDragging(false); handleFile(e.dataTransfer?.files?.[0]) }}>
              <input ref={fileRef} type="file" accept=".xlsx,.docx,.pdf" className="hidden"
                     onChange={e => handleFile(e.target.files?.[0])} />
              {file ? (
                <>
                  <div className="w-12 h-12 rounded-xl flex items-center justify-center mb-3"
                       style={{ background: 'rgba(34,197,94,0.15)', border: '1px solid rgba(34,197,94,0.3)' }}>
                    <Icon name="doc" size={22} color="#16a34a" />
                  </div>
                  <p className="font-semibold" style={{ color: t.text }}>{file.name}</p>
                  <p className="text-sm mt-1" style={{ color: t.text3 }}>{(file.size / 1024).toFixed(0)} KB · Click to change</p>
                </>
              ) : (
                <>
                  <div className="w-12 h-12 rounded-xl flex items-center justify-center mb-3"
                       style={{ background: t.dark ? 'rgba(59,130,246,0.1)' : '#eff6ff' }}>
                    <Icon name="upload" size={22} color={t.primary} />
                  </div>
                  <p className="font-semibold" style={{ color: t.text }}>Drop your questionnaire file here</p>
                  <p className="text-sm mt-1" style={{ color: t.text3 }}>Click to browse · XLSX, DOCX, PDF</p>
                </>
              )}
            </div>

            <div className={`grid gap-4 ${isCompany ? 'grid-cols-1' : 'grid-cols-2'}`}>
              <div>
                <label className="block text-xs font-semibold mb-1.5" style={{ color: t.text2 }}>
                  Questionnaire name <span className="text-red-500">*</span>
                </label>
                <input value={name} onChange={e => setName(e.target.value)}
                       placeholder="Acme Security Assessment" className={inputCls} style={inputStyle}
                       onFocus={e => e.target.style.boxShadow = `0 0 0 2px ${t.primary}40`}
                       onBlur={e => e.target.style.boxShadow = 'none'} />
              </div>
              {!isCompany && (
                <div>
                  <label className="block text-xs font-semibold mb-1.5" style={{ color: t.text2 }}>
                    Customer / Vendor <span className="text-xs font-normal" style={{ color: t.text3 }}>(optional)</span>
                  </label>
                  <input value={customer} onChange={e => setCustomer(e.target.value)}
                         placeholder="Acme Corp" className={inputCls} style={inputStyle}
                         list="client-suggestions"
                         onFocus={e => e.target.style.boxShadow = `0 0 0 2px ${t.primary}40`}
                         onBlur={e => e.target.style.boxShadow = 'none'} />
                  <datalist id="client-suggestions">
                    {clients.map(c => <option key={c} value={c} />)}
                  </datalist>
                </div>
              )}
            </div>

            <button type="submit" disabled={uploading || !file}
                    className="w-full flex items-center justify-center gap-2 py-3 rounded-xl text-sm font-semibold
                               text-white hover:opacity-90 disabled:opacity-40 transition-all"
                    style={{ background: t.primary }}>
              {uploading ? <><span className="spin inline-block">↻</span> Analysing…</> : <>Continue <Icon name="chevronR" size={14} color="white" /></>}
            </button>
          </form>
        )}

        {/* Step 2 */}
        {step === 2 && preview && preview.file_type !== 'xlsx' && (
          <form onSubmit={handleStep2} className="space-y-5">
            <div className="rounded-xl p-4" style={t.card}>
              <p className="text-sm font-semibold" style={{ color: t.text }}>{preview.filename}</p>
              <p className="text-xs mt-0.5" style={{ color: t.text3 }}>
                {preview.question_count} questions found
              </p>
              <div className="mt-3 flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-semibold"
                   style={{ background: t.dark ? 'rgba(34,197,94,0.1)' : '#f0fdf4',
                            border: '1px solid rgba(34,197,94,0.3)', color: '#16a34a' }}>
                <Icon name="check" size={12} color="#16a34a" /> Questions extracted — review and confirm
              </div>
            </div>

            <div className="rounded-xl overflow-hidden" style={t.card}>
              <div className="px-4 py-2.5" style={{ borderBottom: `1px solid ${t.borderColor}` }}>
                <p className="text-xs font-semibold" style={{ color: t.text2 }}>Extracted questions (showing first 10)</p>
              </div>
              <div className="divide-y" style={{ borderColor: t.borderColor }}>
                {preview.questions.slice(0, 10).map((q, i) => (
                  <div key={i} className="px-4 py-3 flex gap-3">
                    <span className="text-xs font-bold shrink-0 mt-0.5" style={{ color: t.primary }}>{i + 1}</span>
                    <p className="text-xs leading-relaxed" style={{ color: t.text }}>{q}</p>
                  </div>
                ))}
                {preview.questions.length > 10 && (
                  <div className="px-4 py-3 text-xs" style={{ color: t.text3 }}>
                    + {preview.questions.length - 10} more questions
                  </div>
                )}
              </div>
            </div>

            <button type="submit" disabled={finalizing}
                    className="w-full flex items-center justify-center gap-2 py-3 rounded-xl text-sm font-semibold
                               text-white hover:opacity-90 disabled:opacity-40 transition-all"
                    style={{ background: t.primary }}>
              {finalizing ? <><span className="spin inline-block">↻</span> Creating…</> : <>Confirm & create questionnaire <Icon name="chevronR" size={14} color="white" /></>}
            </button>
          </form>
        )}

        {step === 2 && preview && preview.file_type === 'xlsx' && (
          <form onSubmit={handleStep2} className="space-y-5">
            <div className="rounded-xl p-4" style={t.card}>
              <p className="text-sm font-semibold" style={{ color: t.text }}>{preview.filename}</p>
              <p className="text-xs mt-0.5" style={{ color: t.text3 }}>
                {preview.preview.total_rows} rows · {preview.preview.sheet_name}
              </p>
              {preview.suggested_template && (
                <div className="mt-3 flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-semibold"
                     style={{ background: t.dark ? 'rgba(59,130,246,0.1)' : '#eff6ff',
                              border: `1px solid ${t.dark ? 'rgba(59,130,246,0.2)' : 'rgba(59,130,246,0.3)'}`,
                              color: t.primary }}>
                  <Icon name="spark" size={12} color={t.primary} /> Template detected — columns pre-selected
                </div>
              )}
            </div>

            <div>
              <p className="text-xs font-semibold mb-2" style={{ color: t.text3 }}>
                Click headers to assign columns — <span style={{ color: t.primary }}>blue = Questions</span> · <span style={{ color: '#8b5cf6' }}>purple = Yes/No Answer</span> · <span style={{ color: '#16a34a' }}>green = Evidence/Comments</span>
              </p>
              <div className="rounded-xl overflow-hidden" style={t.card}>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs">
                    <thead>
                      <tr style={{ borderBottom: `1px solid ${t.borderColor}` }}>
                        {preview.preview.columns.map((col, ci) => {
                          const isQ = questionCol === ci
                          const isA = answerCol === ci
                          const isE = evidenceCol === ci
                          const bg = isQ ? (t.dark ? 'rgba(59,130,246,0.15)' : '#eff6ff')
                                   : isA ? (t.dark ? 'rgba(139,92,246,0.15)' : '#f5f3ff')
                                   : isE ? (t.dark ? 'rgba(22,163,74,0.15)' : '#f0fdf4')
                                   : 'transparent'
                          const color = isQ ? t.primary : isA ? '#7c3aed' : isE ? '#16a34a' : t.text3
                          return (
                            <th key={ci} className="px-4 py-3 text-left font-semibold cursor-pointer transition-all select-none"
                                style={{ background: bg, color, borderRight: `1px solid ${t.borderColor}` }}
                                onClick={() => {
                                  if (isQ) { setQuestionCol(null); return }
                                  if (isA) { setAnswerCol(null); return }
                                  if (isE) { setEvidenceCol(null); return }
                                  if (questionCol === null) { setQuestionCol(ci); return }
                                  if (answerCol === null) { setAnswerCol(ci); return }
                                  if (evidenceCol === null) { setEvidenceCol(ci); return }
                                }}>
                              <div className="flex items-center gap-1.5">
                                {isQ && <span className="px-1.5 py-0.5 rounded text-[9px] font-black"
                                              style={{ background: t.dark ? 'rgba(59,130,246,0.2)' : '#dbeafe', color: t.primary }}>Q</span>}
                                {isA && <span className="px-1.5 py-0.5 rounded text-[9px] font-black"
                                              style={{ background: t.dark ? 'rgba(139,92,246,0.2)' : '#ede9fe', color: '#7c3aed' }}>A</span>}
                                {isE && <span className="px-1.5 py-0.5 rounded text-[9px] font-black"
                                              style={{ background: t.dark ? 'rgba(22,163,74,0.2)' : '#dcfce7', color: '#16a34a' }}>E</span>}
                                {!isQ && !isA && !isE && <span style={{ color: t.text3 }}>{ci}</span>}
                                <span className="truncate max-w-[100px]">{col}</span>
                              </div>
                            </th>
                          )
                        })}
                      </tr>
                    </thead>
                    <tbody>
                      {preview.preview.sample_rows.slice(0, 4).map((row, ri) => (
                        <tr key={ri} style={{ borderBottom: `1px solid ${t.borderColor}` }}>
                          {row.map((cell, ci) => (
                            <td key={ci} className="px-4 py-2.5 max-w-[140px]"
                                style={{ color: t.text3, borderRight: `1px solid ${t.borderColor}`,
                                         background: questionCol === ci ? (t.dark ? 'rgba(59,130,246,0.04)' : '#f0f7ff')
                                                   : answerCol === ci ? (t.dark ? 'rgba(139,92,246,0.04)' : '#faf5ff')
                                                   : evidenceCol === ci ? (t.dark ? 'rgba(22,163,74,0.04)' : '#f0fdf4')
                                                   : 'transparent' }}>
                              <span className="block truncate">{cell || <span style={{ color: t.text3 }}>—</span>}</span>
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>

            <div className="flex gap-2">
              {[
                { label: 'Questions', col: questionCol, accent: t.primary },
                { label: 'Yes/No Answer', col: answerCol, accent: '#7c3aed' },
                { label: 'Evidence/Comments', col: evidenceCol, accent: '#16a34a', optional: true },
              ].map(s => (
                <div key={s.label} className="flex-1 px-3 py-2.5 rounded-xl text-xs font-medium"
                     style={{ background: s.col !== null ? `${s.accent}10` : t.dark ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.03)',
                              border: `1px solid ${s.col !== null ? s.accent + '30' : t.borderColor}`,
                              color: s.col !== null ? s.accent : t.text3 }}>
                  <span className="font-semibold">{s.label}{s.optional ? ' (optional)' : ''}:</span>{' '}
                  {s.col !== null ? `Col ${s.col} — ${preview.preview.columns[s.col]}` : 'Not selected'}
                </div>
              ))}
            </div>

            {questionCol !== null && answerCol === null && (
              <div className="px-4 py-3 rounded-xl text-xs font-medium"
                   style={{ background: 'rgba(245,158,11,0.08)', border: '1px solid rgba(245,158,11,0.3)', color: '#92400e' }}>
                No answer column selected — answers will be written to a new column on export.
              </div>
            )}

            <button type="submit" disabled={finalizing || questionCol === null}
                    className="w-full flex items-center justify-center gap-2 py-3 rounded-xl text-sm font-semibold
                               text-white hover:opacity-90 disabled:opacity-40 transition-all"
                    style={{ background: t.primary }}>
              {finalizing ? <><span className="spin inline-block">↻</span> Creating…</> : <><Icon name="check" size={14} color="white" /> Create Questionnaire</>}
            </button>
          </form>
        )}

        {/* Step 3 */}
        {step === 3 && result && (
          <div className="fade-in rounded-xl py-16 text-center"
               style={{ background: 'rgba(34,197,94,0.06)', border: '1px solid rgba(34,197,94,0.2)' }}>
            <div className="w-14 h-14 rounded-xl mx-auto mb-4 flex items-center justify-center"
                 style={{ background: 'rgba(34,197,94,0.15)', border: '1px solid rgba(34,197,94,0.3)' }}>
              <Icon name="check" size={28} color="#16a34a" />
            </div>
            <h2 className="text-xl font-bold mb-2" style={{ color: t.text }}>Questionnaire Created</h2>
            <p className="text-sm" style={{ color: t.text2 }}>
              <strong style={{ color: t.text }}>{result.question_count}</strong> questions imported from{' '}
              <strong style={{ color: t.text }}>{result.name}</strong>
            </p>
            <p className="text-xs mt-2" style={{ color: t.text3 }}>Redirecting…</p>
            <button onClick={() => nav(`/questionnaires/${result.id}`)}
                    className="mt-6 inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold text-white hover:opacity-90"
                    style={{ background: t.primary }}>
              <Icon name="chevronR" size={14} color="white" /> Open Now
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
