import { Navigate, Route, Routes } from 'react-router-dom'
import AppLayout from './layouts/AppLayout'
import AppointmentSummaryPage from './pages/AppointmentSummaryPage'
import AppointmentsPage from './pages/AppointmentsPage'
import DashboardPage from './pages/DashboardPage'
import PatientsPage from './pages/PatientsPage'
import CallHistoryPage from './pages/CallHistoryPage'
import CalendarConnectPage from './pages/CalendarConnectPage'
import SettingsPage from './pages/SettingsPage'
import LoginPage from './pages/LoginPage'
import NotFoundPage from './pages/NotFoundPage'
import OAuthCallbackPage from './pages/OAuthCallbackPage'

const ROUTE_ROOT = '/'
const ROUTE_LOGIN = '/login'
const ROUTE_APP = '/app'
const ROUTE_OAUTH_CALLBACK = '/oauth/callback'
const ROUTE_DASHBOARD = 'dashboard'
const ROUTE_APPOINTMENTS = 'appointments'
const ROUTE_PATIENTS = 'patients'
const ROUTE_CALLS = 'calls'
const ROUTE_CALENDAR = 'calendar'
const ROUTE_SETTINGS = 'settings'
const ROUTE_FALLBACK = '*'

const App = () => {
  return (
    <Routes>
      <Route path={ROUTE_ROOT} element={<Navigate to={ROUTE_LOGIN} replace />} />
      <Route path={ROUTE_LOGIN} element={<LoginPage />} />
      <Route path={ROUTE_OAUTH_CALLBACK} element={<OAuthCallbackPage />} />
      <Route path={ROUTE_APP} element={<AppLayout />}>
        <Route index element={<AppointmentSummaryPage />} />
        <Route path={ROUTE_DASHBOARD} element={<DashboardPage />} />
        <Route path={ROUTE_APPOINTMENTS} element={<AppointmentsPage />} />
        <Route path={ROUTE_PATIENTS} element={<PatientsPage />} />
        <Route path={ROUTE_CALLS} element={<CallHistoryPage />} />
        <Route path={ROUTE_CALENDAR} element={<CalendarConnectPage />} />
        <Route path={ROUTE_SETTINGS} element={<SettingsPage />} />
      </Route>
      <Route path={ROUTE_FALLBACK} element={<NotFoundPage />} />
    </Routes>
  )
}

export default App
