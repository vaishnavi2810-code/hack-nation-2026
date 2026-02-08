import { Navigate, Route, Routes } from 'react-router-dom'
import AppLayout from './layouts/AppLayout'
import AppointmentSummaryPage from './pages/AppointmentSummaryPage'
import LoginPage from './pages/LoginPage'
import NotFoundPage from './pages/NotFoundPage'
import OAuthCallbackPage from './pages/OAuthCallbackPage'

const ROUTE_ROOT = '/'
const ROUTE_LOGIN = '/login'
const ROUTE_APP = '/app'
const ROUTE_OAUTH_CALLBACK = '/oauth/callback'
const ROUTE_FALLBACK = '*'

const App = () => {
  return (
    <Routes>
      <Route path={ROUTE_ROOT} element={<Navigate to={ROUTE_LOGIN} replace />} />
      <Route path={ROUTE_LOGIN} element={<LoginPage />} />
      <Route path={ROUTE_OAUTH_CALLBACK} element={<OAuthCallbackPage />} />
      <Route path={ROUTE_APP} element={<AppLayout />}>
        <Route index element={<AppointmentSummaryPage />} />
      </Route>
      <Route path={ROUTE_FALLBACK} element={<NotFoundPage />} />
    </Routes>
  )
}

export default App
