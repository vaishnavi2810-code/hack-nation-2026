import { Link } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { CalendarCheck, CheckCircle2, HeartPulse, Lock, ShieldCheck } from 'lucide-react'
import StatusBadge from '../components/StatusBadge'
import { apiRequest, API_PATHS, ERRORS, HTTP } from '../lib/api'

type CalendarStatus = {
  connected: boolean
  calendar_id?: string | null
  email?: string | null
  connected_at?: string | null
}

const CONNECT_TITLE = 'Connect Google Calendar'
const CONNECT_SUBTITLE = 'Link your clinic calendar to sync availability and appointments.'
const STATUS_LABEL_CONNECTED = 'Connected'
const STATUS_LABEL_DISCONNECTED = 'Not connected'
const STATUS_LABEL_ERROR = 'Connection error'
const STATUS_LABEL_AUTH_REQUIRED = 'Add access token to check status'
const BUTTON_AUTHORIZE = 'Authorize Calendar'
const BUTTON_DISCONNECT = 'Disconnect calendar'
const BUTTON_LOADING = 'Loading...'
const ERROR_LOAD_STATUS = 'Unable to load calendar status.'
const ERROR_AUTHORIZE = 'Unable to start Google authorization.'
const ERROR_DISCONNECT = 'Unable to disconnect calendar.'
const EMPTY_VALUE = '—'

const steps = [
  'Authorize access to your clinic Google Calendar.',
  'Check connection status and disconnect anytime.',
  'Use availability lookups when booking appointments.',
]

const CalendarConnectPage = () => {
  const [calendarStatus, setCalendarStatus] = useState<CalendarStatus | null>(null)
  const [statusMessage, setStatusMessage] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  const loadCalendarStatus = async () => {
    setIsLoading(true)
    const result = await apiRequest<CalendarStatus>(API_PATHS.CALENDAR_STATUS, {
      method: HTTP.GET,
      requiresAuth: true,
    })

    if (result.error) {
      setStatusMessage(result.error === ERRORS.MISSING_TOKEN ? STATUS_LABEL_AUTH_REQUIRED : ERROR_LOAD_STATUS)
      setCalendarStatus(null)
    } else if (result.data) {
      setCalendarStatus(result.data)
      setStatusMessage(null)
    }
    setIsLoading(false)
  }

  useEffect(() => {
    loadCalendarStatus()
  }, [])

  const handleAuthorize = async () => {
    setIsLoading(true)
    const result = await apiRequest<{ auth_url: string }>(API_PATHS.AUTH_GOOGLE_URL, {
      method: HTTP.GET,
    })
    setIsLoading(false)

    if (result.error || !result.data?.auth_url) {
      setStatusMessage(ERROR_AUTHORIZE)
      return
    }

    window.location.assign(result.data.auth_url)
  }

  const handleDisconnect = async () => {
    setIsLoading(true)
    const result = await apiRequest<{ success: boolean }>(API_PATHS.CALENDAR_DISCONNECT, {
      method: HTTP.POST,
      requiresAuth: true,
      body: {},
    })
    setIsLoading(false)

    if (result.error || !result.data?.success) {
      setStatusMessage(ERROR_DISCONNECT)
      return
    }

    loadCalendarStatus()
  }

  const statusLabel = calendarStatus?.connected ? STATUS_LABEL_CONNECTED : STATUS_LABEL_DISCONNECTED
  const statusVariant = calendarStatus?.connected ? 'success' : 'warning'
  const statusBadgeLabel =
    statusMessage === STATUS_LABEL_AUTH_REQUIRED
      ? STATUS_LABEL_AUTH_REQUIRED
      : statusMessage
        ? STATUS_LABEL_ERROR
        : statusLabel
  const statusBadgeVariant =
    statusMessage === STATUS_LABEL_AUTH_REQUIRED ? 'info' : statusMessage ? 'warning' : statusVariant

  return (
    <div className="min-h-screen bg-background px-6 py-12">
      <div className="mx-auto max-w-3xl">
        <Link to="/" className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10 text-primary">
            <HeartPulse className="h-5 w-5" />
          </div>
          <div>
            <p className="text-lg font-semibold text-slate-900">MomMode</p>
            <p className="text-xs text-slate-500">Google Calendar connection</p>
          </div>
        </Link>

        <div className="mt-8 grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
          <div className="rounded-3xl border border-slate-200 bg-white p-8 shadow-soft">
            <div className="flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-primary/10 text-primary">
                <CalendarCheck className="h-5 w-5" />
              </div>
              <div>
                <h1 className="text-2xl font-semibold text-slate-900">{CONNECT_TITLE}</h1>
                <p className="text-sm text-slate-600">{CONNECT_SUBTITLE}</p>
              </div>
            </div>

            <div className="mt-6 space-y-4 text-sm text-slate-600">
              {steps.map((step) => (
                <div key={step} className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-success" />
                  {step}
                </div>
              ))}
            </div>

            <div className="mt-8 space-y-3">
              <button
                type="button"
                onClick={handleAuthorize}
                className="block w-full rounded-full bg-primary px-6 py-3 text-center text-sm font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-70"
                disabled={isLoading}
              >
                {isLoading ? BUTTON_LOADING : BUTTON_AUTHORIZE}
              </button>
              {calendarStatus?.connected && (
                <button
                  type="button"
                  onClick={handleDisconnect}
                  className="block w-full rounded-full border border-slate-200 px-6 py-3 text-center text-sm font-semibold text-slate-600 transition hover:border-primary hover:text-primary disabled:cursor-not-allowed disabled:opacity-70"
                  disabled={isLoading}
                >
                  {isLoading ? BUTTON_LOADING : BUTTON_DISCONNECT}
                </button>
              )}
            </div>
            <p className="mt-3 text-xs text-slate-500">
              Admin-only connection. Patients never access this portal.
            </p>
            <div className="mt-6 rounded-2xl border border-slate-100 bg-slate-50 px-4 py-4 text-sm text-slate-600">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Connection status</p>
                  <p className="mt-1 text-sm font-semibold text-slate-900">
                    {statusMessage ?? statusLabel}
                  </p>
                </div>
                <StatusBadge label={statusBadgeLabel} variant={statusBadgeVariant} />
              </div>
              <div className="mt-3 grid gap-2 text-xs text-slate-500">
                <div className="flex items-center justify-between">
                  <span>Calendar ID</span>
                  <span className="font-semibold text-slate-600">
                    {calendarStatus?.calendar_id ?? EMPTY_VALUE}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span>Email</span>
                  <span className="font-semibold text-slate-600">{calendarStatus?.email ?? EMPTY_VALUE}</span>
                </div>
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-soft">
              <div className="flex items-center gap-3">
                <ShieldCheck className="h-5 w-5 text-primary" />
                <p className="text-sm font-semibold text-slate-900">Security first</p>
              </div>
              <p className="mt-3 text-sm text-slate-600">
                MomMode stores appointment metadata in Google Calendar and limits access to
                authorized clinic staff.
              </p>
            </div>
            <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-soft">
              <div className="flex items-center gap-3">
                <Lock className="h-5 w-5 text-success" />
                <p className="text-sm font-semibold text-slate-900">HIPAA-conscious workflows</p>
              </div>
              <p className="mt-3 text-sm text-slate-600">
                Every call summary is audit-ready and stored in your secure clinic workspace.
              </p>
            </div>
            <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-soft">
              <p className="text-sm font-semibold text-slate-900">Need help?</p>
              <p className="mt-3 text-sm text-slate-600">
                Reach out to your MomMode onboarding specialist for calendar and call routing
                support.
              </p>
              <Link to="/login" className="mt-4 inline-flex text-sm font-semibold text-primary">
                Return to login
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default CalendarConnectPage
