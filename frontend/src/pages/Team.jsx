import { useState, useEffect } from 'react'
import { api } from '../api'
import { useAuth } from '../context/AuthContext'
import { useTheme } from '../context/ThemeContext'
import { Icon } from '../components/Layout'

const ROLE_STYLE = {
  owner:  { bg: 'rgba(245,158,11,0.12)',  color: '#f59e0b',  border: 'rgba(245,158,11,0.25)'  },
  admin:  { bg: 'rgba(59,130,246,0.12)',  color: '#3b82f6',  border: 'rgba(59,130,246,0.25)'  },
  member: { bg: 'rgba(100,116,139,0.12)', color: '#64748b',  border: 'rgba(100,116,139,0.25)' },
}

function RoleBadge({ role }) {
  const s = ROLE_STYLE[role] || ROLE_STYLE.member
  return (
    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold"
          style={{ background: s.bg, color: s.color, border: `1px solid ${s.border}` }}>
      {role}
    </span>
  )
}

export default function Team() {
  const { t } = useTheme()
  const { user: me, login } = useAuth()
  const [members, setMembers] = useState([])
  const [loading, setLoading] = useState(true)
  const [changing, setChanging] = useState(null) // user_id being changed
  const [confirm, setConfirm] = useState(null)   // { userId, name, newRole }
  const [error, setError] = useState('')

  const isOwner = me?.role === 'owner'

  const load = () => {
    setLoading(true)
    api.getTeam().then(setMembers).catch(console.error).finally(() => setLoading(false))
  }
  useEffect(load, [])

  const handleRoleChange = (member, newRole) => {
    if (newRole === member.role) return
    setConfirm({ userId: member.id, name: member.full_name || member.email, newRole })
  }

  const confirmChange = async () => {
    if (!confirm) return
    setChanging(confirm.userId)
    setError('')
    try {
      const res = await api.changeRole(confirm.userId, confirm.newRole)
      if (res.detail) { setError(res.detail); setConfirm(null); setChanging(null); return }
      // If ownership transferred, update local auth state with new role
      if (res.you) {
        const stored = JSON.parse(localStorage.getItem('sentinel_user') || '{}')
        localStorage.setItem('sentinel_user', JSON.stringify({ ...stored, role: res.you.role }))
        // Force page reload so auth context picks up the new role
        window.location.reload()
        return
      }
      setConfirm(null)
      load()
    } catch (e) {
      setError('Failed to change role.')
    }
    setChanging(null)
  }

  return (
    <div className="h-full overflow-y-auto">
      <div className="p-8 max-w-3xl mx-auto">

        <div className="mb-8">
          <h1 className="text-2xl font-bold" style={{ color: t.text }}>Team</h1>
          <p className="text-sm mt-0.5" style={{ color: t.text2 }}>
            Manage your workspace members and roles
          </p>
        </div>

        {/* Invite code box */}
        <div className="rounded-xl p-5 mb-6" style={t.card}>
          <p className="text-xs font-semibold mb-1" style={{ color: t.text3 }}>Invite teammates</p>
          <p className="text-sm mb-3" style={{ color: t.text2 }}>
            Share your workspace invite code — anyone who registers with it joins as a member.
          </p>
          <div className="flex items-center gap-3">
            <code className="flex-1 px-3 py-2 rounded-lg text-sm font-mono font-semibold"
                  style={{ background: t.dark ? 'rgba(255,255,255,0.06)' : '#f1f5f9',
                           color: t.primary, border: `1px solid ${t.borderColor}` }}>
              {me?.org_slug}
            </code>
            <button
              onClick={() => { navigator.clipboard.writeText(me?.org_slug || ''); }}
              className="px-3 py-2 rounded-lg text-xs font-semibold transition-opacity hover:opacity-70"
              style={{ background: t.dark ? 'rgba(59,130,246,0.12)' : '#eff6ff',
                       color: t.primary, border: `1px solid ${t.dark ? 'rgba(59,130,246,0.2)' : 'rgba(59,130,246,0.3)'}` }}>
              Copy
            </button>
          </div>
        </div>

        {error && (
          <div className="mb-4 px-4 py-3 rounded-xl text-sm font-medium"
               style={{ background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)', color: '#ef4444' }}>
            {error}
          </div>
        )}

        {/* Confirm modal */}
        {confirm && (
          <div className="fixed inset-0 z-50 flex items-center justify-center"
               style={{ background: 'rgba(0,0,0,0.5)' }}
               onClick={() => setConfirm(null)}>
            <div className="rounded-2xl p-6 w-full max-w-sm mx-4" style={t.card}
                 onClick={e => e.stopPropagation()}>
              <h3 className="text-base font-bold mb-2" style={{ color: t.text }}>
                {confirm.newRole === 'owner' ? 'Transfer ownership?' : 'Change role?'}
              </h3>
              <p className="text-sm mb-5" style={{ color: t.text2 }}>
                {confirm.newRole === 'owner'
                  ? <>You will become <strong>admin</strong> and <strong>{confirm.name}</strong> will become the new <strong>owner</strong>. This cannot be undone without their cooperation.</>
                  : <>Change <strong>{confirm.name}</strong> to <strong>{confirm.newRole}</strong>?</>
                }
              </p>
              <div className="flex gap-3">
                <button onClick={() => setConfirm(null)}
                        className="flex-1 py-2 rounded-xl text-sm font-semibold transition-opacity hover:opacity-70"
                        style={{ background: t.dark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)', color: t.text2 }}>
                  Cancel
                </button>
                <button onClick={confirmChange} disabled={!!changing}
                        className="flex-1 py-2 rounded-xl text-sm font-semibold text-white transition-opacity hover:opacity-90 disabled:opacity-50"
                        style={{ background: confirm.newRole === 'owner' ? '#f59e0b' : t.primary }}>
                  {changing ? 'Saving…' : 'Confirm'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Members table */}
        {loading ? (
          <div className="space-y-2">{[...Array(3)].map((_, i) => <div key={i} className="skeleton h-14 rounded-xl" />)}</div>
        ) : (
          <div className="rounded-xl overflow-hidden" style={t.card}>
            <table className="w-full text-sm">
              <thead>
                <tr style={{ background: t.tableHead, borderBottom: `1px solid ${t.borderColor}` }}>
                  {['Member', 'Role', 'Joined', isOwner ? 'Change Role' : ''].filter(Boolean).map(h => (
                    <th key={h} className="px-5 py-3 text-left text-xs font-semibold" style={{ color: t.text3 }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {members.map(m => {
                  const isMe = m.id === me?.id
                  return (
                    <tr key={m.id} className="transition-colors"
                        style={{ borderBottom: `1px solid ${t.borderColor}` }}
                        onMouseEnter={e => e.currentTarget.style.background = t.surfaceHover}
                        onMouseLeave={e => e.currentTarget.style.background = 'transparent'}>
                      <td className="px-5 py-4">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold text-white flex-shrink-0"
                               style={{ background: t.primary }}>
                            {(m.full_name || m.email)[0].toUpperCase()}
                          </div>
                          <div>
                            <p className="font-semibold" style={{ color: t.text }}>
                              {m.full_name || m.email}
                              {isMe && <span className="ml-2 text-[10px] font-medium" style={{ color: t.text3 }}>(you)</span>}
                            </p>
                            {m.full_name && <p className="text-xs" style={{ color: t.text3 }}>{m.email}</p>}
                          </div>
                        </div>
                      </td>
                      <td className="px-5 py-4"><RoleBadge role={m.role} /></td>
                      <td className="px-5 py-4 text-xs" style={{ color: t.text3 }}>
                        {new Date(m.created_at).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })}
                      </td>
                      {isOwner && (
                        <td className="px-5 py-4">
                          {isMe ? (
                            <span className="text-xs" style={{ color: t.text3 }}>—</span>
                          ) : (
                            <select
                              value={m.role}
                              onChange={e => handleRoleChange(m, e.target.value)}
                              disabled={!!changing}
                              className="text-xs rounded-lg px-2 py-1.5 outline-none font-semibold transition-all disabled:opacity-50"
                              style={{ ...t.input, color: t.text, cursor: 'pointer' }}>
                              <option value="member">member</option>
                              <option value="admin">admin</option>
                              <option value="owner">owner (transfer)</option>
                            </select>
                          )}
                        </td>
                      )}
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}

        <p className="text-xs mt-3 px-1" style={{ color: t.text3 }}>
          {members.length} member{members.length !== 1 ? 's' : ''} · Invite code: <code style={{ color: t.primary }}>{me?.org_slug}</code>
        </p>
      </div>
    </div>
  )
}
