import { Outlet, NavLink, useLocation, useNavigate } from 'react-router-dom'
import { useState, useEffect, useRef } from 'react'
import { useAuth } from '../context/AuthContext'
import { useTheme } from '../context/ThemeContext'
import { api } from '../api'

// ── SVG icon system ─────────────────────────────────────────────────────────
export function Icon({ name, size = 16, color = 'currentColor' }) {
  const paths = {
    shield:    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75m-3-7.036A11.959 11.959 0 0 1 3.598 6 11.99 11.99 0 0 0 3 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285Z"/>,
    clipboard: <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 0 0 2.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 0 0-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 0 0 .75-.75 2.25 2.25 0 0 0-.1-.664m-5.8 0A2.251 2.251 0 0 1 13.5 2.25H15c1.012 0 1.867.668 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25Z"/>,
    book:      <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 0 0 6 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 0 1 6 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 0 1 6-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0 0 18 18a8.967 8.967 0 0 0-6 2.292m0-14.25v14.25"/>,
    archive:   <path strokeLinecap="round" strokeLinejoin="round" d="m20.25 7.5-.625 10.632a2.25 2.25 0 0 1-2.247 2.118H6.622a2.25 2.25 0 0 1-2.247-2.118L3.75 7.5M10 11.25h4M3.375 7.5h17.25c.621 0 1.125-.504 1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125Z"/>,
    grid:      <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6A2.25 2.25 0 0 1 6 3.75h2.25A2.25 2.25 0 0 1 10.5 6v2.25a2.25 2.25 0 0 1-2.25 2.25H6a2.25 2.25 0 0 1-2.25-2.25V6ZM3.75 15.75A2.25 2.25 0 0 1 6 13.5h2.25a2.25 2.25 0 0 1 2.25 2.25V18a2.25 2.25 0 0 1-2.25 2.25H6A2.25 2.25 0 0 1 3.75 18v-2.25ZM13.5 6a2.25 2.25 0 0 1 2.25-2.25H18A2.25 2.25 0 0 1 20.25 6v2.25A2.25 2.25 0 0 1 18 10.5h-2.25a2.25 2.25 0 0 1-2.25-2.25V6ZM13.5 15.75a2.25 2.25 0 0 1 2.25-2.25H18a2.25 2.25 0 0 1 2.25 2.25V18A2.25 2.25 0 0 1 18 20.25h-2.25A2.25 2.25 0 0 1 13.5 18v-2.25Z"/>,
    chart:     <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z"/>,
    user:      <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0ZM4.501 20.118a7.5 7.5 0 0 1 14.998 0A17.933 17.933 0 0 1 12 21.75c-2.676 0-5.216-.584-7.499-1.632Z"/>,
    chevronR:  <path strokeLinecap="round" strokeLinejoin="round" d="m8.25 4.5 7.5 7.5-7.5 7.5"/>,
    chevronD:  <path strokeLinecap="round" strokeLinejoin="round" d="m19.5 8.25-7.5 7.5-7.5-7.5"/>,
    arrowL:    <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5 3 12m0 0 7.5-7.5M3 12h18"/>,
    check:     <path strokeLinecap="round" strokeLinejoin="round" d="m4.5 12.75 6 6 9-13.5"/>,
    x:         <path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12"/>,
    spark:     <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09Z"/>,
    upload:    <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5m-13.5-9L12 3m0 0 4.5 4.5M12 3v13.5"/>,
    download:  <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5M16.5 12 12 16.5m0 0L7.5 12m4.5 4.5V3"/>,
    trash:     <path strokeLinecap="round" strokeLinejoin="round" d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 0 1-2.244 2.077H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0"/>,
    plus:      <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15"/>,
    refresh:   <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0 3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182m0-4.991v4.99"/>,
    search:    <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z"/>,
    doc:       <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z"/>,
    clock:     <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z"/>,
    bolt:      <path strokeLinecap="round" strokeLinejoin="round" d="m3.75 13.5 10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75Z"/>,
    sun:       <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v2.25m6.364.386-1.591 1.591M21 12h-2.25m-.386 6.364-1.591-1.591M12 18.75V21m-4.773-4.227-1.591 1.591M5.25 12H3m4.227-4.773L5.636 5.636M15.75 12a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0Z"/>,
    moon:      <path strokeLinecap="round" strokeLinejoin="round" d="M21.752 15.002A9.72 9.72 0 0 1 18 15.75c-5.385 0-9.75-4.365-9.75-9.75 0-1.33.266-2.597.748-3.752A9.753 9.753 0 0 0 3 11.25C3 16.635 7.365 21 12.75 21a9.753 9.753 0 0 0 9.002-5.998Z"/>,
    logout:    <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 9V5.25A2.25 2.25 0 0 0 13.5 3h-6a2.25 2.25 0 0 0-2.25 2.25v13.5A2.25 2.25 0 0 0 7.5 21h6a2.25 2.25 0 0 0 2.25-2.25V15M12 9l-3 3m0 0 3 3m-3-3h12.75"/>,
    chat:      <path strokeLinecap="round" strokeLinejoin="round" d="M8.625 9.75a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0H8.25m4.125 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0H12m4.125 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0h-.375m-13.5 3.01c0 1.6 1.123 2.994 2.707 3.227 1.087.16 2.185.283 3.293.369V21l4.184-4.183a1.14 1.14 0 0 1 .778-.332 48.294 48.294 0 0 0 5.83-.498c1.585-.233 2.708-1.626 2.708-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.394 48.394 0 0 0 12 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v6.018Z"/>,
    inbox:     <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 13.5h3.86a2.25 2.25 0 0 1 2.012 1.244l.256.512a2.25 2.25 0 0 0 2.013 1.244h3.218a2.25 2.25 0 0 0 2.013-1.244l.256-.512a2.25 2.25 0 0 1 2.013-1.244h3.859m-19.5.338V18a2.25 2.25 0 0 0 2.25 2.25h15A2.25 2.25 0 0 0 21.75 18v-4.162c0-.224-.034-.447-.1-.661L19.24 5.338a2.25 2.25 0 0 0-2.15-1.588H6.911a2.25 2.25 0 0 0-2.15 1.588L2.1 13.177a2.25 2.25 0 0 0-.1.661Z"/>,
    bell:      <path strokeLinecap="round" strokeLinejoin="round" d="M14.857 17.082a23.848 23.848 0 0 0 5.454-1.31A8.967 8.967 0 0 1 18 9.75V9A6 6 0 0 0 6 9v.75a8.967 8.967 0 0 1-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 0 1-5.714 0m5.714 0a3 3 0 1 1-5.714 0"/>,
  }
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
         stroke={color} strokeWidth="1.75" style={{ flexShrink: 0 }}>
      {paths[name] || null}
    </svg>
  )
}

// ── Nav config ───────────────────────────────────────────────────────────────
const NAV_SECTIONS = [
  {
    items: [
      { to: '/',                        label: 'Dashboard',      icon: 'chart',     exact: true },
    ]
  },
  {
    label: 'Work',
    items: [
      { to: '/questionnaires',          label: 'Questionnaires', icon: 'clipboard', match: (p) => p.startsWith('/questionnaires') && p !== '/questionnaires/templates' },
      { to: '/assignments',             label: 'My Assignments', icon: 'inbox',     match: (p) => p === '/assignments' },
      { to: '/knowledge',               label: 'Knowledge Base', icon: 'book',      match: (p) => p.startsWith('/knowledge') && p !== '/knowledge/health' },
      { to: '/knowledge/health',        label: 'KB Health',      icon: 'chart',     match: (p) => p === '/knowledge/health' },
      { to: '/answers/library',         label: 'Answer Library', icon: 'archive',   match: (p) => p.startsWith('/answers') },
      { to: '/questionnaires/templates',label: 'Templates',      icon: 'grid',      match: (p) => p === '/questionnaires/templates' },
    ]
  },
  {
    label: 'Account',
    items: [
      { to: '/account/password', label: 'Change Password', icon: 'shield', match: (p) => p === '/account/password' },
    ]
  },
  {
    label: 'Analytics',
    adminOnly: true,
    items: [
      { to: '/admin/audit',             label: 'Audit Log',      icon: 'clock',     match: (p) => p === '/admin/audit' },
      { to: '/trash',                   label: 'Trash',          icon: 'doc',       match: (p) => p === '/trash',        adminOnly: true },
      { to: '/admin/team',              label: 'Team',           icon: 'user',      match: (p) => p === '/admin/team'  },
    ]
  },
]

function NavItem({ item, pathname, t }) {
  const isActive = item.exact ? pathname === item.to : (item.match ? item.match(pathname) : pathname.startsWith(item.to))
  return (
    <NavLink to={item.to}
      className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-semibold transition-all duration-150 group"
      style={{
        background: isActive ? (t.dark ? 'rgba(59,130,246,0.12)' : 'rgba(37,99,235,0.08)') : 'transparent',
        color: isActive ? t.primary : t.text,
      }}
      onMouseEnter={e => { if (!isActive) e.currentTarget.style.background = t.dark ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.04)' }}
      onMouseLeave={e => { if (!isActive) e.currentTarget.style.background = 'transparent' }}>
      <Icon name={item.icon} size={16} color={isActive ? t.primary : t.text} />
      <span>{item.label}</span>
      {isActive && (
        <span className="ml-auto w-1.5 h-1.5 rounded-full flex-shrink-0" style={{ background: t.primary }} />
      )}
    </NavLink>
  )
}

export default function Layout() {
  const { pathname } = useLocation()
  const { user, logout } = useAuth()
  const nav = useNavigate()
  const { t, toggle } = useTheme()
  const [showInvite, setShowInvite] = useState(false)
  const [notifications, setNotifications] = useState([])
  const [unread, setUnread] = useState(0)
  const [showNotifs, setShowNotifs] = useState(false)
  const notifRef = useRef(null)

  const handleLogout = () => { logout(); nav('/login', { replace: true }) }

  const loadNotifs = () => {
    api.getNotifications()
      .then(d => { setNotifications(d.notifications); setUnread(d.unread) })
      .catch(() => {})
  }

  useEffect(() => {
    loadNotifs()
    const interval = setInterval(loadNotifs, 30000)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    const handler = (e) => { if (notifRef.current && !notifRef.current.contains(e.target)) setShowNotifs(false) }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const handleMarkAllRead = async () => {
    await api.markAllNotificationsRead()
    setNotifications(p => p.map(n => ({ ...n, read: true })))
    setUnread(0)
  }

  const handleMarkRead = async (id) => {
    await api.markNotificationRead(id)
    setNotifications(p => p.map(n => n.id === id ? { ...n, read: true } : n))
    setUnread(p => Math.max(0, p - 1))
  }

  const fmtNotifTime = (iso) => {
    const d = new Date(iso)
    const diff = Date.now() - d
    if (diff < 60000) return 'Just now'
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`
    return d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })
  }

  const initials = user?.full_name
    ? user.full_name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
    : user?.email?.[0]?.toUpperCase() || '?'

  return (
    <div className="h-screen flex overflow-hidden" style={{ background: t.bg }}>

      {/* ── Sidebar ──────────────────────────────────────────────────────── */}
      <aside
        className="w-[224px] shrink-0 h-screen flex flex-col z-20"
        style={{
          background: t.sidebar,
          borderRight: `1px solid ${t.sidebarBorder}`,
        }}>

        {/* Logo */}
        <div className="px-4 py-5 flex items-center gap-3"
             style={{ borderBottom: `1px solid ${t.sidebarBorder}` }}>
          <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
               style={{ background: t.primary }}>
            <Icon name="shield" size={15} color="white" />
          </div>
          <div>
            <p className="font-bold text-sm leading-none" style={{ color: t.text }}>Greenlight</p>
            <p className="text-xs mt-0.5" style={{ color: t.text3 }}>Close deals faster</p>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-3 py-4 space-y-5 overflow-y-auto">
          {NAV_SECTIONS.filter(s => !s.adminOnly || user?.role === 'owner' || user?.role === 'admin').map((section, si) => (
            <div key={si}>
              {section.label && (
                <p className="text-[10px] font-semibold uppercase tracking-widest px-3 mb-1.5"
                   style={{ color: t.text3 }}>
                  {section.label}
                </p>
              )}
              <div className="space-y-0.5">
                {section.items.map(item => (
                  <NavItem key={item.to} item={item} pathname={pathname} t={t} />
                ))}
              </div>
            </div>
          ))}
        </nav>

        {/* Notifications */}
        <div className="px-3 py-2 relative" ref={notifRef} style={{ borderTop: `1px solid ${t.sidebarBorder}` }}>
          <button
            onClick={() => setShowNotifs(s => !s)}
            className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium transition-all"
            style={{ color: t.text3 }}
            onMouseEnter={e => e.currentTarget.style.background = t.dark ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.04)'}
            onMouseLeave={e => e.currentTarget.style.background = 'transparent'}>
            <div className="relative flex-shrink-0">
              <Icon name="bell" size={14} color={t.text3} />
              {unread > 0 && (
                <span className="absolute -top-1 -right-1 w-3.5 h-3.5 rounded-full text-[8px] font-bold flex items-center justify-center text-white"
                      style={{ background: '#ef4444' }}>
                  {unread > 9 ? '9+' : unread}
                </span>
              )}
            </div>
            Notifications
          </button>

          {showNotifs && (
            <div className="absolute bottom-full left-3 right-3 mb-1 rounded-xl shadow-2xl z-50 overflow-hidden"
                 style={{ ...t.card, border: `1px solid ${t.borderColor}` }}>
              <div className="flex items-center justify-between px-3 py-2.5"
                   style={{ borderBottom: `1px solid ${t.borderColor}` }}>
                <span className="text-xs font-semibold" style={{ color: t.text }}>Notifications</span>
                {unread > 0 && (
                  <button onClick={handleMarkAllRead}
                          className="text-[10px] font-semibold hover:opacity-70 transition-opacity"
                          style={{ color: t.primary }}>
                    Mark all read
                  </button>
                )}
              </div>
              <div className="max-h-64 overflow-y-auto">
                {notifications.length === 0 ? (
                  <p className="text-xs text-center py-6" style={{ color: t.text3 }}>No notifications</p>
                ) : notifications.map(n => (
                  <div key={n.id}
                       className="px-3 py-2.5 cursor-pointer transition-colors"
                       style={{
                         background: n.read ? 'transparent' : (t.dark ? 'rgba(59,130,246,0.06)' : 'rgba(37,99,235,0.04)'),
                         borderBottom: `1px solid ${t.borderColor}`,
                       }}
                       onClick={() => {
                         if (!n.read) handleMarkRead(n.id)
                         if (n.resource_type === 'questionnaire' && n.resource_id) {
                           nav(`/questionnaires/${n.resource_id}`)
                           setShowNotifs(false)
                         }
                       }}
                       onMouseEnter={e => e.currentTarget.style.background = t.dark ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.03)'}
                       onMouseLeave={e => e.currentTarget.style.background = n.read ? 'transparent' : (t.dark ? 'rgba(59,130,246,0.06)' : 'rgba(37,99,235,0.04)')}>
                    <div className="flex items-start gap-2">
                      {!n.read && (
                        <div className="w-1.5 h-1.5 rounded-full mt-1 flex-shrink-0" style={{ background: t.primary }} />
                      )}
                      <div className={!n.read ? '' : 'pl-3.5'}>
                        <p className="text-[11px] font-semibold leading-snug" style={{ color: t.text }}>{n.title}</p>
                        {n.body && <p className="text-[10px] mt-0.5 leading-snug" style={{ color: t.text3 }}>{n.body}</p>}
                        <p className="text-[10px] mt-0.5" style={{ color: t.text3 }}>{fmtNotifTime(n.created_at)}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Bottom: invite code */}
        <div className="px-3 py-3" style={{ borderTop: `1px solid ${t.sidebarBorder}` }}>
          <button
            onClick={() => setShowInvite(s => !s)}
            className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium transition-all"
            style={{ color: t.text3 }}
            onMouseEnter={e => e.currentTarget.style.background = t.dark ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.04)'}
            onMouseLeave={e => e.currentTarget.style.background = 'transparent'}>
            <Icon name="user" size={14} color={t.text3} />
            Invite teammates
          </button>
          {showInvite && (
            <div className="mt-2 px-3 py-2.5 rounded-lg text-xs fade-in"
                 style={{ background: t.dark ? 'rgba(255,255,255,0.04)' : '#f8fafc', border: `1px solid ${t.borderColor}` }}>
              <p className="font-semibold mb-1" style={{ color: t.text2 }}>Invite code</p>
              <code className="font-mono font-bold" style={{ color: t.primary }}>
                {user?.org_slug || '—'}
              </code>
            </div>
          )}
        </div>

        {/* Bottom: user + theme toggle */}
        <div className="px-3 pb-4 space-y-1" style={{ borderTop: `1px solid ${t.sidebarBorder}`, paddingTop: '12px' }}>

          {/* Theme toggle */}
          <button
            onClick={toggle}
            className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium transition-all"
            style={{ color: t.text3 }}
            onMouseEnter={e => e.currentTarget.style.background = t.dark ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.04)'}
            onMouseLeave={e => e.currentTarget.style.background = 'transparent'}>
            <Icon name={t.dark ? 'sun' : 'moon'} size={14} color={t.text3} />
            {t.dark ? 'Light mode' : 'Dark mode'}
          </button>

          {/* User */}
          <div className="flex items-center gap-2.5 px-3 py-2 rounded-lg"
               style={{ background: t.dark ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.03)' }}>
            <div className="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold text-white flex-shrink-0"
                 style={{ background: t.primary }}>
              {initials}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-1.5">
                <p className="text-xs font-semibold truncate leading-tight" style={{ color: t.text }}>
                  {user?.full_name || user?.email}
                </p>
                <span className="text-[9px] font-bold px-1.5 py-0.5 rounded flex-shrink-0"
                      style={{
                        background: user?.role === 'owner' ? 'rgba(245,158,11,0.15)' : user?.role === 'admin' ? 'rgba(59,130,246,0.15)' : 'rgba(100,116,139,0.15)',
                        color: user?.role === 'owner' ? '#f59e0b' : user?.role === 'admin' ? '#3b82f6' : '#64748b',
                      }}>
                  {user?.role}
                </span>
              </div>
              <p className="text-[10px] truncate" style={{ color: t.text3 }}>
                {user?.org_name}
              </p>
            </div>
            <button onClick={handleLogout} title="Sign out"
                    className="flex-shrink-0 transition-opacity hover:opacity-70">
              <Icon name="logout" size={14} color={t.text3} />
            </button>
          </div>
        </div>
      </aside>

      {/* ── Main content ─────────────────────────────────────────────────── */}
      <main className="flex-1 overflow-hidden flex flex-col relative">
        {user && !user.email_verified && (
          <EmailVerificationBanner />
        )}
        <div className="flex-1 overflow-y-auto">
          <Outlet />
        </div>
      </main>
    </div>
  )
}

function EmailVerificationBanner() {
  const { t } = useTheme()
  const [sent, setSent] = useState(false)
  const [sending, setSending] = useState(false)

  const handleResend = async () => {
    setSending(true)
    try {
      await api.resendVerification()
      setSent(true)
    } catch { /* silent */ }
    setSending(false)
  }

  return (
    <div className="flex-shrink-0 flex items-center justify-between gap-4 px-5 py-2.5 text-xs font-medium"
         style={{ background: 'rgba(245,158,11,0.1)', borderBottom: '1px solid rgba(245,158,11,0.25)', color: '#92400e' }}>
      <span>Please verify your email address to secure your account.</span>
      {sent ? (
        <span style={{ color: '#16a34a' }}>Verification email sent — check your inbox.</span>
      ) : (
        <button onClick={handleResend} disabled={sending}
                className="font-semibold underline hover:opacity-70 disabled:opacity-40 flex-shrink-0">
          {sending ? 'Sending…' : 'Resend verification email'}
        </button>
      )}
    </div>
  )
}
