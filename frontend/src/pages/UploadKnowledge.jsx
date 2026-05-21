import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'
import { useTheme } from '../context/ThemeContext'
import { Icon } from '../components/Layout'

const ACCEPTED = {
  pdf:  { label: 'PDF',  color: '#ef4444', bg: 'rgba(239,68,68,0.1)',  border: 'rgba(239,68,68,0.25)'  },
  docx: { label: 'DOCX', color: '#3b82f6', bg: 'rgba(59,130,246,0.1)', border: 'rgba(59,130,246,0.25)' },
}

export default function UploadKnowledge() {
  const { t } = useTheme()
  const nav = useNavigate()
  const fileRef = useRef()
  const [file, setFile] = useState(null)
  const [dragging, setDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)

  const handleFile = (f) => {
    if (!f) return
    const ext = f.name.split('.').pop().toLowerCase()
    if (!['pdf', 'docx'].includes(ext)) { setError('Only PDF and DOCX files are supported.'); return }
    setError(''); setFile(f)
  }

  const handleUpload = async () => {
    if (!file || uploading) return
    setError(''); setUploading(true)
    try {
      const fd = new FormData(); fd.append('file', file)
      const data = await api.uploadKnowledge(fd)
      setResult(data)
      setTimeout(() => nav('/knowledge'), 2500)
    } catch (e) {
      setError(e.message || 'Upload failed.')
    }
    setUploading(false)
  }

  const ext = file ? file.name.split('.').pop().toLowerCase() : null
  const fc = ext ? ACCEPTED[ext] : null

  return (
    <div className="h-full overflow-y-auto">
      <div className="p-8 max-w-2xl mx-auto">

        <button onClick={() => nav('/knowledge')}
                className="flex items-center gap-1.5 text-xs font-medium mb-6 transition-opacity hover:opacity-70"
                style={{ color: t.text3 }}>
          <Icon name="arrowL" size={12} color={t.text3} /> Knowledge Base
        </button>

        <h1 className="text-2xl font-bold mb-1" style={{ color: t.text }}>Upload Document</h1>
        <p className="text-sm mb-8" style={{ color: t.text2 }}>
          Add security policies and documentation to improve answer accuracy.
        </p>

        {error && (
          <div className="mb-5 px-4 py-3 rounded-xl text-sm font-medium"
               style={{ background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)', color: '#ef4444' }}>
            {error}
          </div>
        )}

        {!result ? (
          <div className="space-y-4">
            {/* Format info */}
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold" style={{ color: t.text3 }}>Accepted:</span>
              {Object.entries(ACCEPTED).map(([k, v]) => (
                <span key={k} className="px-2.5 py-1 rounded text-xs font-semibold"
                      style={{ background: v.bg, border: `1px solid ${v.border}`, color: v.color }}>
                  {v.label}
                </span>
              ))}
            </div>

            {/* Drop zone */}
            <div className="rounded-xl border-2 border-dashed transition-all cursor-pointer flex flex-col items-center justify-center py-14 text-center"
                 style={{
                   borderColor: dragging ? t.primary : file ? '#22c55e' : t.borderColor,
                   background: dragging ? `${t.primary}08` : file ? 'rgba(34,197,94,0.04)' : t.dark ? 'rgba(255,255,255,0.02)' : 'rgba(0,0,0,0.02)',
                 }}
                 onClick={() => !uploading && fileRef.current?.click()}
                 onDragOver={e => { e.preventDefault(); setDragging(true) }}
                 onDragLeave={() => setDragging(false)}
                 onDrop={e => { e.preventDefault(); setDragging(false); handleFile(e.dataTransfer?.files?.[0]) }}>
              <input ref={fileRef} type="file" accept=".pdf,.docx" className="hidden"
                     onChange={e => handleFile(e.target.files?.[0])} />
              {file ? (
                <>
                  <div className="w-12 h-12 rounded-xl flex items-center justify-center mb-3"
                       style={{ background: fc?.bg, border: `1px solid ${fc?.border}` }}>
                    <Icon name="doc" size={22} color={fc?.color} />
                  </div>
                  <p className="font-semibold" style={{ color: t.text }}>{file.name}</p>
                  <p className="text-sm mt-1" style={{ color: t.text3 }}>
                    {(file.size / 1024).toFixed(0)} KB · <span style={{ color: fc?.color }}>{ext?.toUpperCase()}</span> · Click to change
                  </p>
                </>
              ) : (
                <>
                  <div className="w-12 h-12 rounded-xl flex items-center justify-center mb-3"
                       style={{ background: t.dark ? 'rgba(59,130,246,0.1)' : '#eff6ff' }}>
                    <Icon name="upload" size={22} color={t.primary} />
                  </div>
                  <p className="font-semibold" style={{ color: t.text }}>Drop your document here</p>
                  <p className="text-sm mt-1" style={{ color: t.text3 }}>PDF or DOCX · Click to browse</p>
                </>
              )}
            </div>

            {/* Info */}
            <div className="px-4 py-3.5 rounded-xl"
                 style={{ background: t.dark ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.03)',
                          border: `1px solid ${t.borderColor}` }}>
              <p className="text-xs leading-relaxed" style={{ color: t.text3 }}>
                <strong style={{ color: t.text2 }}>What happens:</strong> The document is parsed, split into chunks, and embedded.
                Those chunks are retrieved when generating answers to questionnaire questions.
              </p>
            </div>

            <button onClick={handleUpload} disabled={!file || uploading}
                    className="w-full flex items-center justify-center gap-2 py-3 rounded-xl text-sm font-semibold
                               text-white hover:opacity-90 disabled:opacity-40 transition-all"
                    style={{ background: t.primary }}>
              {uploading
                ? <><span className="spin inline-block">↻</span> Processing…</>
                : <><Icon name="upload" size={14} color="white" /> Upload & Process</>}
            </button>
          </div>
        ) : (
          <div className="fade-in rounded-xl py-16 text-center"
               style={{ background: 'rgba(34,197,94,0.06)', border: '1px solid rgba(34,197,94,0.2)' }}>
            <div className="w-14 h-14 rounded-xl mx-auto mb-4 flex items-center justify-center"
                 style={{ background: 'rgba(34,197,94,0.15)', border: '1px solid rgba(34,197,94,0.3)' }}>
              <Icon name="check" size={28} color="#16a34a" />
            </div>
            <h2 className="text-xl font-bold mb-2" style={{ color: t.text }}>Document Uploaded</h2>
            <p className="text-sm" style={{ color: t.text2 }}>
              <strong style={{ color: t.text }}>{result.filename}</strong> processed into{' '}
              <strong style={{ color: t.text }}>{result.chunk_count}</strong> searchable chunks
            </p>
            <button onClick={() => nav('/knowledge')}
                    className="mt-6 inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold text-white hover:opacity-90"
                    style={{ background: t.primary }}>
              <Icon name="book" size={14} color="white" /> View Knowledge Base
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
