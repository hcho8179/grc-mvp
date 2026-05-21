import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import { ThemeProvider } from './context/ThemeContext'
import ProtectedRoute from './components/ProtectedRoute'
import Layout from './components/Layout'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import QuestionnairsList from './pages/QuestionnairsList'
import QuestionnaireDetail from './pages/QuestionnaireDetail'
import UploadQuestionnaire from './pages/UploadQuestionnaire'
import KnowledgeBase from './pages/KnowledgeBase'
import UploadKnowledge from './pages/UploadKnowledge'
import AnswerLibrary from './pages/AnswerLibrary'
import Templates from './pages/Templates'
import UsagePage from './pages/UsagePage'
import AuditLog from './pages/AuditLog'
import Team from './pages/Team'
import ForgotPassword from './pages/ForgotPassword'
import ResetPassword from './pages/ResetPassword'
import ChangePassword from './pages/ChangePassword'
import MyAssignments from './pages/MyAssignments'
import KBHealth from './pages/KBHealth'
import VerifyEmail from './pages/VerifyEmail'
import Trash from './pages/Trash'

export default function App() {
  return (
    <BrowserRouter>
      <ThemeProvider>
      <AuthProvider>
        <Routes>
          {/* Public auth routes */}
          <Route path="/login"           element={<Login />} />
          <Route path="/register"        element={<Register />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />
          <Route path="/reset-password"  element={<ResetPassword />} />
          <Route path="/verify-email"    element={<VerifyEmail />} />

          {/* Protected app routes */}
          <Route element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }>
            <Route index element={<Dashboard />} />
            <Route path="questionnaires" element={<QuestionnairsList />} />
            <Route path="questionnaires/upload" element={<UploadQuestionnaire />} />
            <Route path="questionnaires/templates" element={<Templates />} />
            <Route path="questionnaires/:id" element={<QuestionnaireDetail />} />
            <Route path="assignments" element={<MyAssignments />} />
            <Route path="knowledge" element={<KnowledgeBase />} />
            <Route path="knowledge/health" element={<KBHealth />} />
            <Route path="knowledge/upload" element={<UploadKnowledge />} />
            <Route path="answers/library" element={<AnswerLibrary />} />
            <Route path="admin/usage" element={<UsagePage />} />
            <Route path="admin/audit" element={<AuditLog />} />
            <Route path="admin/team"            element={<Team />} />
            <Route path="account/password"      element={<ChangePassword />} />
            <Route path="trash"                 element={<Trash />} />
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
      </ThemeProvider>
    </BrowserRouter>
  )
}
