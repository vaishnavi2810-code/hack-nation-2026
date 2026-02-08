import { useEffect, useState } from 'react'
import { Bell, Building2, CalendarDays } from 'lucide-react'
import { Link } from 'react-router-dom'
import { apiRequest, API_PATHS, clearSessionTokens, getAccessToken, getRefreshToken, getUserId, HTTP, storeSessionTokens } from '../lib/api'

type SettingsResponse = {
  appointment_duration_minutes: number
  reminder_hours_before: number
  timezone: string
  enable_sms_confirmations: boolean
  enable_reminders: boolean
  enable_outbound_calls: boolean
}

const PAGE_TITLE = 'Settings'
const PAGE_SUBTITLE = 'Update clinic settings and notification preferences.'
const SECTION_CLINIC_SETTINGS = 'Clinic settings'
const SECTION_NOTIFICATIONS = 'Notification preferences'
const SECTION_CALENDAR = 'Calendar connection'
const SECTION_SESSION = 'API session'

const FIELD_CLINIC_NAME = 'Clinic name'
const FIELD_TIMEZONE = 'Timezone'
const FIELD_APPOINTMENT_LENGTH = 'Default appointment length (minutes)'
const FIELD_REMINDER_HOURS = 'Reminder hours before appointment'
const FIELD_CLINIC_PHONE = 'Clinic contact phone'

const LABEL_SAVE_SETTINGS = 'Save settings'
const LABEL_SAVE_SESSION = 'Save session tokens'
const LABEL_CLEAR_SESSION = 'Clear session tokens'
const LABEL_LOADING = 'Saving...'

const STATUS_LOADING = 'Loading settings...'
const STATUS_LOAD_ERROR = 'Unable to load settings.'
const STATUS_SAVE_ERROR = 'Unable to save settings.'
const STATUS_SESSION_ERROR = 'Unable to save session tokens.'
const STATUS_SESSION_SAVED = 'Session tokens saved.'
const STATUS_SESSION_CLEARED = 'Session tokens cleared.'

const TIMEZONE_OPTIONS = [
  { label: 'Pacific (US)', value: 'America/Los_Angeles' },
  { label: 'Mountain (US)', value: 'America/Denver' },
  { label: 'Central (US)', value: 'America/Chicago' },
  { label: 'Eastern (US)', value: 'America/New_York' },
]
const DEFAULT_TIMEZONE = TIMEZONE_OPTIONS[0]?.value ?? EMPTY_VALUE

const SESSION_FIELD_ACCESS_TOKEN = 'Access token'
const SESSION_FIELD_REFRESH_TOKEN = 'Refresh token'
const SESSION_FIELD_USER_ID = 'User ID'
const SESSION_FIELD_EXPIRES_IN = 'Expires in (seconds)'

const DEFAULT_TOKEN_TYPE = 'bearer'
const DEFAULT_EXPIRES_IN = 1800
const EMPTY_VALUE = ''

const SettingsPage = () => {
  const [settings, setSettings] = useState<SettingsResponse | null>(null)
  const [clinicName, setClinicName] = useState(EMPTY_VALUE)
  const [clinicPhone, setClinicPhone] = useState(EMPTY_VALUE)
  const [statusMessage, setStatusMessage] = useState<string | null>(null)
  const [isSaving, setIsSaving] = useState(false)
  const [sessionAccessToken, setSessionAccessToken] = useState(getAccessToken() ?? EMPTY_VALUE)
  const [sessionRefreshToken, setSessionRefreshToken] = useState(getRefreshToken() ?? EMPTY_VALUE)
  const [sessionUserId, setSessionUserId] = useState(getUserId() ?? EMPTY_VALUE)
  const [sessionExpiresIn, setSessionExpiresIn] = useState(String(DEFAULT_EXPIRES_IN))

  const loadSettings = async () => {
    setStatusMessage(STATUS_LOADING)
    const result = await apiRequest<SettingsResponse>(API_PATHS.SETTINGS, { method: HTTP.GET })

    if (result.error || !result.data) {
      setStatusMessage(STATUS_LOAD_ERROR)
      return
    }

    setSettings(result.data)
    setStatusMessage(null)
  }

  useEffect(() => {
    loadSettings()
  }, [])

  const handleSaveSettings = async () => {
    if (!settings) {
      return
    }
    setIsSaving(true)
    const result = await apiRequest<SettingsResponse>(API_PATHS.SETTINGS, {
      method: HTTP.PUT,
      body: {
        appointment_duration_minutes: settings.appointment_duration_minutes,
        reminder_hours_before: settings.reminder_hours_before,
        timezone: settings.timezone,
        enable_sms_confirmations: settings.enable_sms_confirmations,
        enable_reminders: settings.enable_reminders,
        enable_outbound_calls: settings.enable_outbound_calls,
      },
    })
    setIsSaving(false)

    if (result.error || !result.data) {
      setStatusMessage(STATUS_SAVE_ERROR)
      return
    }

    setSettings(result.data)
    setStatusMessage(null)
  }

  const handleSaveSessionTokens = () => {
    if (!sessionAccessToken) {
      setStatusMessage(STATUS_SESSION_ERROR)
      return
    }

    storeSessionTokens({
      access_token: sessionAccessToken,
      refresh_token: sessionRefreshToken,
      token_type: DEFAULT_TOKEN_TYPE,
      expires_in: Number(sessionExpiresIn) || DEFAULT_EXPIRES_IN,
      user_id: sessionUserId || undefined,
    })

    setStatusMessage(STATUS_SESSION_SAVED)
  }

  const handleClearSession = () => {
    clearSessionTokens()
    setSessionAccessToken(EMPTY_VALUE)
    setSessionRefreshToken(EMPTY_VALUE)
    setSessionUserId(EMPTY_VALUE)
    setSessionExpiresIn(String(DEFAULT_EXPIRES_IN))
    setStatusMessage(STATUS_SESSION_CLEARED)
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">{PAGE_TITLE}</h1>
        <p className="mt-1 text-sm text-slate-600">{PAGE_SUBTITLE}</p>
        {statusMessage && <p className="mt-3 text-sm text-slate-600">{statusMessage}</p>}
      </div>

      <form className="space-y-6">
        <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-soft">
          <div className="flex items-center gap-3">
            <Building2 className="h-5 w-5 text-primary" />
            <h2 className="text-base font-semibold text-slate-900">{SECTION_CLINIC_SETTINGS}</h2>
          </div>
          <div className="mt-4 grid gap-4 md:grid-cols-2">
            <label className="block text-sm font-semibold text-slate-700">
              {FIELD_CLINIC_NAME}
              <input
                type="text"
                placeholder="Summit Family Clinic"
                value={clinicName}
                onChange={(event) => setClinicName(event.target.value)}
                className="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm text-slate-700 outline-none transition focus:border-primary focus:bg-white"
              />
            </label>
            <label className="block text-sm font-semibold text-slate-700">
              {FIELD_TIMEZONE}
              <select
                value={settings?.timezone ?? DEFAULT_TIMEZONE}
                onChange={(event) =>
                  setSettings((prev) => (prev ? { ...prev, timezone: event.target.value } : prev))
                }
                className="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm text-slate-700 outline-none transition focus:border-primary focus:bg-white"
              >
                {TIMEZONE_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
            <label className="block text-sm font-semibold text-slate-700">
              {FIELD_APPOINTMENT_LENGTH}
              <input
                type="number"
                min="10"
                step="5"
                placeholder="30"
                value={settings?.appointment_duration_minutes ?? EMPTY_VALUE}
                onChange={(event) =>
                  setSettings((prev) =>
                    prev
                      ? {
                          ...prev,
                          appointment_duration_minutes: Number(event.target.value),
                        }
                      : prev,
                  )
                }
                className="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm text-slate-700 outline-none transition focus:border-primary focus:bg-white"
              />
            </label>
            <label className="block text-sm font-semibold text-slate-700">
              {FIELD_REMINDER_HOURS}
              <input
                type="number"
                min="1"
                step="1"
                placeholder="3"
                value={settings?.reminder_hours_before ?? EMPTY_VALUE}
                onChange={(event) =>
                  setSettings((prev) =>
                    prev
                      ? {
                          ...prev,
                          reminder_hours_before: Number(event.target.value),
                        }
                      : prev,
                  )
                }
                className="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm text-slate-700 outline-none transition focus:border-primary focus:bg-white"
              />
            </label>
            <label className="block text-sm font-semibold text-slate-700">
              {FIELD_CLINIC_PHONE}
              <input
                type="tel"
                placeholder="(555) 555-0199"
                value={clinicPhone}
                onChange={(event) => setClinicPhone(event.target.value)}
                className="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm text-slate-700 outline-none transition focus:border-primary focus:bg-white"
              />
            </label>
          </div>
        </div>

        <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-soft">
          <div className="flex items-center gap-3">
            <Bell className="h-5 w-5 text-success" />
            <h2 className="text-base font-semibold text-slate-900">{SECTION_NOTIFICATIONS}</h2>
          </div>
          <div className="mt-4 space-y-3 text-sm text-slate-600">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={settings?.enable_sms_confirmations ?? false}
                onChange={(event) =>
                  setSettings((prev) =>
                    prev ? { ...prev, enable_sms_confirmations: event.target.checked } : prev,
                  )
                }
                className="h-4 w-4 rounded border-slate-300"
              />
              Enable SMS confirmations
            </label>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={settings?.enable_reminders ?? false}
                onChange={(event) =>
                  setSettings((prev) =>
                    prev ? { ...prev, enable_reminders: event.target.checked } : prev,
                  )
                }
                className="h-4 w-4 rounded border-slate-300"
              />
              Enable appointment reminders
            </label>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={settings?.enable_outbound_calls ?? false}
                onChange={(event) =>
                  setSettings((prev) =>
                    prev ? { ...prev, enable_outbound_calls: event.target.checked } : prev,
                  )
                }
                className="h-4 w-4 rounded border-slate-300"
              />
              Enable outbound calls
            </label>
          </div>
        </div>

        <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-soft">
          <div className="flex items-center gap-3">
            <CalendarDays className="h-5 w-5 text-primary" />
            <h2 className="text-base font-semibold text-slate-900">{SECTION_CALENDAR}</h2>
          </div>
          <p className="mt-3 text-sm text-slate-600">
            Manage Google Calendar access to keep availability and appointments in sync.
          </p>
          <Link
            to="/connect-calendar"
            className="mt-4 inline-flex rounded-full border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-600 transition hover:border-primary hover:text-primary"
          >
            Manage calendar connection
          </Link>
        </div>

        <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-soft">
          <div className="flex items-center gap-3">
            <CalendarDays className="h-5 w-5 text-primary" />
            <h2 className="text-base font-semibold text-slate-900">{SECTION_SESSION}</h2>
          </div>
          <p className="mt-3 text-sm text-slate-600">
            Store JWT session tokens to authenticate protected API calls.
          </p>
          <div className="mt-4 grid gap-4 md:grid-cols-2">
            <label className="block text-sm font-semibold text-slate-700">
              {SESSION_FIELD_ACCESS_TOKEN}
              <input
                type="password"
                value={sessionAccessToken}
                onChange={(event) => setSessionAccessToken(event.target.value)}
                className="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm text-slate-700 outline-none transition focus:border-primary focus:bg-white"
              />
            </label>
            <label className="block text-sm font-semibold text-slate-700">
              {SESSION_FIELD_REFRESH_TOKEN}
              <input
                type="password"
                value={sessionRefreshToken}
                onChange={(event) => setSessionRefreshToken(event.target.value)}
                className="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm text-slate-700 outline-none transition focus:border-primary focus:bg-white"
              />
            </label>
            <label className="block text-sm font-semibold text-slate-700">
              {SESSION_FIELD_USER_ID}
              <input
                type="text"
                value={sessionUserId}
                onChange={(event) => setSessionUserId(event.target.value)}
                className="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm text-slate-700 outline-none transition focus:border-primary focus:bg-white"
              />
            </label>
            <label className="block text-sm font-semibold text-slate-700">
              {SESSION_FIELD_EXPIRES_IN}
              <input
                type="number"
                min="60"
                step="60"
                value={sessionExpiresIn}
                onChange={(event) => setSessionExpiresIn(event.target.value)}
                className="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm text-slate-700 outline-none transition focus:border-primary focus:bg-white"
              />
            </label>
          </div>
          <div className="mt-4 flex flex-wrap gap-3">
            <button
              type="button"
              onClick={handleSaveSessionTokens}
              className="rounded-full border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-600 transition hover:border-primary hover:text-primary"
            >
              {LABEL_SAVE_SESSION}
            </button>
            <button
              type="button"
              onClick={handleClearSession}
              className="rounded-full border border-rose-200 px-4 py-2 text-xs font-semibold text-rose-500 transition hover:border-rose-300"
            >
              {LABEL_CLEAR_SESSION}
            </button>
          </div>
        </div>

        <div className="flex justify-end">
          <button
            type="button"
            onClick={handleSaveSettings}
            className="rounded-full bg-primary px-6 py-3 text-sm font-semibold text-white transition hover:bg-blue-700"
          >
            {isSaving ? LABEL_LOADING : LABEL_SAVE_SETTINGS}
          </button>
        </div>
      </form>
    </div>
  )
}

export default SettingsPage
