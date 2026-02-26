import { Navigate, Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import { useAuth } from './contexts/AuthContext'
import { canAccessSection, getDefaultRouteForUser } from './config/permissions'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import SchedulesPage from './pages/SchedulesPage'
import ContentPage from './pages/ContentPage'
import GroupsPage from './pages/GroupsPage'
import BellModelPage from './pages/BellModelPage'
import SoundsPage from './pages/SoundsPage'
import AlertsPage from './pages/AlertsPage'
import ReportsPage from './pages/ReportsPage'
import AdminUsersPage from './pages/AdminUsersPage'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth()

  if (loading) return <div>Ladowanie...</div>
  if (!user) return <Navigate to="/login" replace />
  return <Layout>{children}</Layout>
}

function RoleRoute({
  section,
  children,
}: {
  section: Parameters<typeof canAccessSection>[1]
  children: React.ReactNode
}) {
  const { user } = useAuth()
  if (!canAccessSection(user, section)) return <Navigate to={getDefaultRouteForUser(user)} replace />
  return <ProtectedRoute>{children}</ProtectedRoute>
}

function App() {
  const { user, loading } = useAuth()

  if (loading) return <div>Ladowanie...</div>

  return (
    <Routes>
      <Route path="/login" element={!user ? <LoginPage /> : <Navigate to={getDefaultRouteForUser(user)} replace />} />
      <Route path="/" element={<Navigate to={getDefaultRouteForUser(user)} replace />} />
      <Route path="/dashboard" element={<RoleRoute section="dashboard"><DashboardPage /></RoleRoute>} />
      <Route path="/calendar" element={<RoleRoute section="calendar"><SchedulesPage /></RoleRoute>} />
      <Route path="/clients" element={<RoleRoute section="clients"><ContentPage /></RoleRoute>} />
      <Route path="/resources" element={<RoleRoute section="resources"><GroupsPage /></RoleRoute>} />
      <Route path="/services" element={<RoleRoute section="services"><BellModelPage /></RoleRoute>} />
      <Route path="/bundles" element={<RoleRoute section="bundles"><SoundsPage /></RoleRoute>} />
      <Route path="/colors" element={<RoleRoute section="colors"><AlertsPage /></RoleRoute>} />
      <Route path="/reports" element={<RoleRoute section="reports"><ReportsPage /></RoleRoute>} />
      <Route path="/users" element={<RoleRoute section="users"><AdminUsersPage /></RoleRoute>} />
      <Route path="/no-access" element={<ProtectedRoute><div>Brak dostepu do modulow dla tej roli.</div></ProtectedRoute>} />
      <Route path="*" element={<Navigate to={getDefaultRouteForUser(user)} replace />} />
    </Routes>
  )
}

export default App
