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
import Layout from './components/Layout'

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

function App() {
  const { user, loading } = useAuth()

  if (loading) {
    return <div>Ladowanie...</div>
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
      <Route
        path="/displays"
        element={
          <ProtectedRoute>
            <DisplaysPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/displays/:id"
        element={
          <ProtectedRoute>
            <DisplayDetailPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/status"
        element={
          <ProtectedRoute>
            <StatusPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/content"
        element={
          <ProtectedRoute>
            <ContentPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/schedules"
        element={
          <ProtectedRoute>
            <SchedulesPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/groups"
        element={
          <ProtectedRoute>
            <GroupsPage />
          </ProtectedRoute>
        }
      />
      <Route path="/bells/schedules" element={<Navigate to="/bells/model" replace />} />
      <Route
        path="/bells/model"
        element={
          <ProtectedRoute>
            <BellModelPage />
          </ProtectedRoute>
        }
      />
      <Route path="/bells" element={<Navigate to="/bells/schedules" />} />
      <Route
        path="/reports"
        element={
          <ProtectedRoute>
            <ReportsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/alerts"
        element={
          <ProtectedRoute>
            <AlertsPage />
          </ProtectedRoute>
        }
      />
      <Route path="/sounds" element={<Navigate to="/bells/schedules" replace />} />
    </Routes>
  )
}

export default App
