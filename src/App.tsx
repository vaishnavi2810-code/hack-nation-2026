import { Route, Routes } from 'react-router-dom'
import AppLayout from './layouts/AppLayout'
import AppointmentsPage from './pages/AppointmentsPage'
import CalendarConnectPage from './pages/CalendarConnectPage'
import CallHistoryPage from './pages/CallHistoryPage'
import DashboardPage from './pages/DashboardPage'
import DoctorOnboardingPage from './pages/DoctorOnboardingPage'
import LandingPage from './pages/LandingPage'
import LoginPage from './pages/LoginPage'
import NotFoundPage from './pages/NotFoundPage'
import PatientsPage from './pages/PatientsPage'
import SettingsPage from './pages/SettingsPage'

const App = () => {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/onboarding" element={<DoctorOnboardingPage />} />
      <Route path="/connect-calendar" element={<CalendarConnectPage />} />
      <Route path="/app" element={<AppLayout />}>
        <Route index element={<DashboardPage />} />
        <Route path="patients" element={<PatientsPage />} />
        <Route path="appointments" element={<AppointmentsPage />} />
        <Route path="calls" element={<CallHistoryPage />} />
        <Route path="settings" element={<SettingsPage />} />
      </Route>
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}

export default App
