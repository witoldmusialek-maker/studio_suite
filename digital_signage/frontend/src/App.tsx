import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './contexts/AuthContext'
import LoginPage from './pages/LoginPage'
import DisplaysPage from './pages/DisplaysPage'
import DisplayDetailPage from './pages/DisplayDetailPage'
import StatusPage from './pages/StatusPage'
import ContentPage from './pages/ContentPage'
import SchedulesPage from './pages/SchedulesPage'
import GroupsPage from './pages/GroupsPage'
import BellModelPage from './pages/BellModelPage'
import ReportsPage from './pages/ReportsPage'
import AlertsPage from './pages/AlertsPage'
import AdminUsersPage from './pages/AdminUsersPage'
import Layout from './components/Layout'
import { FEATURE_FLAGS } from './config/features'
import { canAccessSection, getDefaultRouteForUser } from './config/permissions'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth()

  if (loading) {
    return <div>Ladowanie...</div>
  }

  if (!user) {
    return <Navigate to="/login" />
  }

  return <Layout>{children}</Layout>
}

function RoleRoute({
  section,
  children,
}: {
  section: Parameters<typeof canAccessSection>[1]
  children: React.ReactNode
}) {
  const { user, loading } = useAuth()

  if (loading) return <div>Ladowanie...</div>
  if (!user) return <Navigate to="/login" replace />
  if (!canAccessSection(user, section)) return <Navigate to={getDefaultRouteForUser(user)} replace />
  return <ProtectedRoute>{children}</ProtectedRoute>
}

function App() {
  const { user, loading } = useAuth()

  if (loading) {
    return <div>Ladowanie...</div>
  }

  return (
    <Routes>
      <Route path="/login" element={!user ? <LoginPage /> : <Navigate to={getDefaultRouteForUser(user)} replace />} />
      <Route path="/" element={<Navigate to={getDefaultRouteForUser(user)} replace />} />
      {FEATURE_FLAGS.displays && canAccessSection(user, 'displays') && (
        <Route
          path="/displays"
          element={
            <RoleRoute section="displays">
              <DisplaysPage />
            </RoleRoute>
          }
        />
      )}
      {FEATURE_FLAGS.displays && canAccessSection(user, 'displays') && (
        <Route
          path="/displays/:id"
          element={
            <RoleRoute section="displays">
              <DisplayDetailPage />
            </RoleRoute>
          }
        />
      )}
      {FEATURE_FLAGS.monitoring && canAccessSection(user, 'monitoring') && (
        <Route
          path="/status"
          element={
            <RoleRoute section="monitoring">
              <StatusPage />
            </RoleRoute>
          }
        />
      )}
      {FEATURE_FLAGS.content && canAccessSection(user, 'content') && (
        <Route
          path="/content"
          element={
            <RoleRoute section="content">
              <ContentPage />
            </RoleRoute>
          }
        />
      )}
      {FEATURE_FLAGS.content && canAccessSection(user, 'schedules') && (
        <Route
          path="/schedules"
          element={
            <RoleRoute section="schedules">
              <SchedulesPage />
            </RoleRoute>
          }
        />
      )}
      {FEATURE_FLAGS.displays && canAccessSection(user, 'groups') && (
        <Route
          path="/groups"
          element={
            <RoleRoute section="groups">
              <GroupsPage />
            </RoleRoute>
          }
        />
      )}
      <Route path="/bells/schedules" element={<Navigate to="/bells/model" replace />} />
      {FEATURE_FLAGS.bells && canAccessSection(user, 'bells') && (
        <Route
          path="/bells/model"
          element={
            <RoleRoute section="bells">
              <BellModelPage />
            </RoleRoute>
          }
        />
      )}
      <Route path="/bells" element={<Navigate to="/bells/model" replace />} />
      {FEATURE_FLAGS.reports && canAccessSection(user, 'reports') && (
        <Route
          path="/reports"
          element={
            <RoleRoute section="reports">
              <ReportsPage />
            </RoleRoute>
          }
        />
      )}
      {FEATURE_FLAGS.alerts && canAccessSection(user, 'alerts') && (
        <Route
          path="/alerts"
          element={
            <RoleRoute section="alerts">
              <AlertsPage />
            </RoleRoute>
          }
        />
      )}
      {FEATURE_FLAGS.adminUsers && canAccessSection(user, 'adminUsers') && (
        <Route
          path="/admin/users"
          element={
            <RoleRoute section="adminUsers">
              <AdminUsersPage />
            </RoleRoute>
          }
        />
      )}
      <Route path="/sounds" element={<Navigate to="/bells/model" replace />} />
      <Route
        path="/no-access"
        element={
          <ProtectedRoute>
            <div>Brak dostepnych modulow dla tej roli lub licencji.</div>
          </ProtectedRoute>
        }
      />
      <Route path="*" element={<Navigate to={getDefaultRouteForUser(user)} replace />} />
    </Routes>
  )
}

export default App
