import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './hooks/useAuth'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import HRDashboard from './pages/HRDashboard'
import { ReactNode } from 'react'

function PrivateRoute({ children }: { children: ReactNode }) {
  const { isAuthenticated } = useAuth()
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />
}

function HRRoute({ children }: { children: ReactNode }) {
  const { isAuthenticated, user } = useAuth()
  if (!isAuthenticated) return <Navigate to="/login" replace />
  if (user?.role !== 'HR') return <Navigate to="/dashboard" replace />
  return <>{children}</>
}

function RoleRedirect() {
  const { user } = useAuth()
  if (user?.role === 'HR') return <Navigate to="/hr" replace />
  return <Navigate to="/dashboard" replace />
}

function AppRoutes() {
  const { isAuthenticated } = useAuth()
  return (
    <Routes>
      <Route
        path="/login"
        element={isAuthenticated ? <RoleRedirect /> : <LoginPage />}
      />
      <Route
        path="/dashboard"
        element={
          <PrivateRoute>
            <DashboardPage />
          </PrivateRoute>
        }
      />
      <Route
        path="/hr"
        element={
          <HRRoute>
            <HRDashboard />
          </HRRoute>
        }
      />
      <Route
        path="/"
        element={isAuthenticated ? <RoleRedirect /> : <Navigate to="/login" replace />}
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </AuthProvider>
  )
}
