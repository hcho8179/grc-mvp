import { createContext, useContext, useState, useEffect } from 'react'

const ThemeContext = createContext()

// Design tokens — one source of truth for both themes
function buildTokens(dark) {
  return {
    dark,
    bg:             dark ? '#0f1117' : '#f0f2f5',
    surface:        dark ? '#161b27' : '#ffffff',
    surfaceHover:   dark ? '#1b2233' : '#f8fafc',
    surfaceActive:  dark ? '#1f2a40' : '#eff6ff',
    borderColor:    dark ? 'rgba(255,255,255,0.07)' : 'rgba(0,0,0,0.08)',
    borderStrong:   dark ? 'rgba(255,255,255,0.13)' : 'rgba(0,0,0,0.14)',
    text:           dark ? '#f1f5f9' : '#0f172a',
    text2:          dark ? '#8b95a8' : '#374151',
    text3:          dark ? '#475569' : '#6b7280',
    sidebar:        dark ? '#0b0e17' : '#ffffff',
    sidebarBorder:  dark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.07)',
    inputBg:        dark ? 'rgba(255,255,255,0.05)' : '#f8fafc',
    inputBorder:    dark ? 'rgba(255,255,255,0.1)'  : 'rgba(0,0,0,0.1)',
    primary:        dark ? '#3b82f6' : '#2563eb',
    primaryHover:   dark ? '#2563eb' : '#1d4ed8',
    shadow:         dark ? '0 1px 3px rgba(0,0,0,0.5)' : '0 1px 3px rgba(0,0,0,0.08),0 1px 2px rgba(0,0,0,0.05)',
    shadowMd:       dark ? '0 4px 16px rgba(0,0,0,0.6)' : '0 4px 12px rgba(0,0,0,0.1)',
    // Shortcuts
    card: {
      background: dark ? '#161b27' : '#ffffff',
      border: `1px solid ${dark ? 'rgba(255,255,255,0.07)' : 'rgba(0,0,0,0.08)'}`,
      boxShadow: dark ? 'none' : '0 1px 3px rgba(0,0,0,0.06)',
    },
    input: {
      background: dark ? 'rgba(255,255,255,0.05)' : '#f8fafc',
      border: `1px solid ${dark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)'}`,
      color: dark ? '#f1f5f9' : '#111827',
    },
    tableBorder: dark ? '1px solid rgba(255,255,255,0.05)' : '1px solid rgba(0,0,0,0.05)',
    tableHead:   dark ? 'rgba(255,255,255,0.02)' : '#f1f5f9',
  }
}

export function ThemeProvider({ children }) {
  const [dark, setDark] = useState(() => {
    const saved = localStorage.getItem('sentinel_theme')
    return saved ? saved === 'dark' : true
  })

  const toggle = () => setDark(d => {
    const next = !d
    localStorage.setItem('sentinel_theme', next ? 'dark' : 'light')
    return next
  })

  useEffect(() => {
    document.body.style.background = dark ? '#0f1117' : '#f0f2f5'
    document.body.style.color      = dark ? '#f1f5f9' : '#111827'
  }, [dark])

  const t = buildTokens(dark)

  return (
    <ThemeContext.Provider value={{ t, toggle }}>
      {children}
    </ThemeContext.Provider>
  )
}

export const useTheme = () => useContext(ThemeContext)
