import { Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useTheme } from '../context/ThemeContext'

export default function ProtectedRoute({ children }) {
  const { user, loading } = useAuth()
  const { t } = useTheme()

  if (loading) return (
    <div className="h-screen flex items-center justify-center" style={{ background: t.bg }}>
      <div className="w-8 h-8 rounded-full border-2 border-t-transparent animate-spin"
           style={{ borderColor: `${t.primary} transparent transparent transparent` }} />
    </div>
  )

  if (!user) return <Navigate to="/login" replace />
  return children
}
