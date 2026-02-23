import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './contexts/AuthContext'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
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

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth()

  if (loading) {
    return <div>Ładowanie...</div>
  }

  if (!user) {
    return <Navigate to="/login" />
  }

  return <Layout>{children}</Layout>
}

function App() {
  const { user, loading } = useAuth()

  if (loading) {
    return <div>Ładowanie...</div>
  }

  return (
    <Routes>
      <Route path="/login" element={!user ? <LoginPage /> : <Navigate to="/" />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <DashboardPage />
          </ProtectedRoute>
        }
      />
      {FEATURE_FLAGS.displays && (
        <Route
          path="/displays"
          element={
            <ProtectedRoute>
              <DisplaysPage />
            </ProtectedRoute>
          }
        />
      )}
      {FEATURE_FLAGS.displays && (
        <Route
          path="/displays/:id"
          element={
            <ProtectedRoute>
              <DisplayDetailPage />
            </ProtectedRoute>
          }
        />
      )}
      {FEATURE_FLAGS.monitoring && (
        <Route
          path="/status"
          element={
            <ProtectedRoute>
              <StatusPage />
            </ProtectedRoute>
          }
        />
      )}
      {FEATURE_FLAGS.content && (
        <Route
          path="/content"
          element={
            <ProtectedRoute>
              <ContentPage />
            </ProtectedRoute>
          }
        />
      )}
      {FEATURE_FLAGS.content && (
        <Route
          path="/schedules"
          element={
            <ProtectedRoute>
              <SchedulesPage />
            </ProtectedRoute>
          }
        />
      )}
      {FEATURE_FLAGS.displays && (
        <Route
          path="/groups"
          element={
            <ProtectedRoute>
              <GroupsPage />
            </ProtectedRoute>
          }
        />
      )}
      <Route path="/bells/schedules" element={<Navigate to="/bells/model" replace />} />
      {FEATURE_FLAGS.bells && (
        <Route
          path="/bells/model"
          element={
            <ProtectedRoute>
              <BellModelPage />
            </ProtectedRoute>
          }
        />
      )}
      <Route path="/bells" element={<Navigate to="/bells/schedules" />} />
      {FEATURE_FLAGS.reports && (
        <Route
          path="/reports"
          element={
            <ProtectedRoute>
              <ReportsPage />
            </ProtectedRoute>
          }
        />
      )}
      {FEATURE_FLAGS.alerts && (
        <Route
          path="/alerts"
          element={
            <ProtectedRoute>
              <AlertsPage />
            </ProtectedRoute>
          }
        />
      )}
      {FEATURE_FLAGS.adminUsers && (
        <Route
          path="/admin/users"
          element={
            <ProtectedRoute>
              <AdminUsersPage />
            </ProtectedRoute>
          }
        />
      )}
      <Route path="/sounds" element={<Navigate to="/bells/schedules" replace />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App
