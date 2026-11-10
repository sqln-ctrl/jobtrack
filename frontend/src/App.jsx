import { Navigate, Outlet, Route, Routes, useLocation } from 'react-router-dom'
import { useAuth } from './context/AuthContext'
import AppLayout from './layouts/AppLayout'
import Login from './pages/Login'
import Onboarding from './pages/Onboarding'
import Overview from './pages/Overview'
import Applications from './pages/Applications'
import ApplicationDetail from './pages/ApplicationDetail'
import Platforms from './pages/Platforms'
import EmailActivity from './pages/EmailActivity'
import Interviews from './pages/Interviews'
import Settings from './pages/Settings'
import { Spinner } from './components/ui'

const onboarded = () => {
  try { return localStorage.getItem('jt_onboarded') === '1' } catch { return true }
}

function Protected() {
  const { user, loading, gmailConnected } = useAuth()
  const { pathname } = useLocation()
  if (loading) return <div className="grid min-h-screen place-items-center"><Spinner /></div>
  if (!user) return <Navigate to="/login" replace />
  if (!gmailConnected && !onboarded() && pathname !== '/onboarding') return <Navigate to="/onboarding" replace />
  return <Outlet />
}

export default function App() {
  const { user, loading } = useAuth()
  return (
    <Routes>
      <Route path="/login" element={!loading && user ? <Navigate to="/" replace /> : <Login />} />
      <Route element={<Protected />}>
        <Route path="/onboarding" element={<Onboarding />} />
        <Route element={<AppLayout />}>
          <Route index element={<Overview />} />
          <Route path="applications" element={<Applications />} />
          <Route path="applications/:id" element={<ApplicationDetail />} />
          <Route path="platforms" element={<Platforms />} />
          <Route path="emails" element={<EmailActivity />} />
          <Route path="interviews" element={<Interviews />} />
          <Route path="settings" element={<Settings />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
