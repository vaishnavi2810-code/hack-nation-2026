const DEFAULT_API_BASE_URL = 'http://localhost:8000'
const ENV_API_BASE_URL = import.meta.env.VITE_API_BASE_URL as string | undefined

const AUTH_HEADER_NAME = 'Authorization'
const BEARER_PREFIX = 'Bearer'
const CONTENT_TYPE_HEADER = 'Content-Type'
const CONTENT_TYPE_JSON = 'application/json'
const EMPTY_STRING = ''

const REQUEST_TIMEOUT_MS = 15000
const MILLISECONDS_PER_SECOND = 1000
const TOKEN_EXPIRY_FALLBACK_SECONDS = 1800

const STORAGE_KEYS = {
  ACCESS_TOKEN: 'callpilot.access_token',
  REFRESH_TOKEN: 'callpilot.refresh_token',
  EXPIRES_AT: 'callpilot.expires_at',
  TOKEN_TYPE: 'callpilot.token_type',
  USER_ID: 'callpilot.user_id',
} as const

const ERROR_MESSAGES = {
  MISSING_TOKEN: 'Missing access token. Add a session token in Settings.',
  NETWORK: 'Network request failed.',
  TIMEOUT: 'Request timed out.',
  INVALID_RESPONSE: 'Unexpected response from API.',
} as const

const HTTP_METHODS = {
  GET: 'GET',
  POST: 'POST',
  PUT: 'PUT',
  DELETE: 'DELETE',
} as const

const sanitizeBaseUrl = (value: string) => value.replace(/\/+$/, '')

type HttpMethod = (typeof HTTP_METHODS)[keyof typeof HTTP_METHODS]

type ApiRequestOptions = {
  method?: HttpMethod
  body?: unknown
  requiresAuth?: boolean
  headers?: Record<string, string>
}

export type ApiResult<T> = {
  data: T | null
  error: string | null
  status: number | null
}

export type TokenResponse = {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  user_id?: string
}

export const API_BASE_URL = sanitizeBaseUrl(ENV_API_BASE_URL ?? DEFAULT_API_BASE_URL)

export const API_PATHS = {
  HEALTH: '/health',
  AUTH_GOOGLE_URL: '/api/auth/google/url',
  AUTH_GOOGLE_CALLBACK: '/api/auth/google/callback',
  AUTH_LOGOUT: '/api/auth/logout',
  DOCTOR_PROFILE: '/api/doctors/me',
  CALENDAR_STATUS: '/api/calendar/status',
  CALENDAR_DISCONNECT: '/api/calendar/disconnect',
  CALENDAR_CHECK_AVAILABILITY: '/api/calendar/check-availability',
  PATIENTS: '/api/patients',
  PATIENT_BY_ID: (patientId: string) => `/api/patients/${patientId}`,
  APPOINTMENTS: '/api/appointments',
  APPOINTMENTS_UPCOMING: '/api/appointments/upcoming',
  APPOINTMENT_BY_ID: (appointmentId: string) => `/api/appointments/${appointmentId}`,
  APPOINTMENT_CONFIRM: (appointmentId: string) => `/api/appointments/${appointmentId}/confirm`,
  CALLS: '/api/calls',
  CALLS_SCHEDULED: '/api/calls/scheduled',
  CALL_BY_ID: (callId: string) => `/api/calls/${callId}`,
  CALLS_MANUAL: '/api/calls/manual',
  DASHBOARD_STATS: '/api/dashboard/stats',
  DASHBOARD_ACTIVITY: '/api/dashboard/activity',
  SETTINGS: '/api/settings',
} as const

export const HTTP = HTTP_METHODS
export const ERRORS = ERROR_MESSAGES

export const getAccessToken = () => getStoredValue(STORAGE_KEYS.ACCESS_TOKEN)
export const getRefreshToken = () => getStoredValue(STORAGE_KEYS.REFRESH_TOKEN)
export const getUserId = () => getStoredValue(STORAGE_KEYS.USER_ID)

export const clearSessionTokens = () => {
  removeStoredValue(STORAGE_KEYS.ACCESS_TOKEN)
  removeStoredValue(STORAGE_KEYS.REFRESH_TOKEN)
  removeStoredValue(STORAGE_KEYS.EXPIRES_AT)
  removeStoredValue(STORAGE_KEYS.TOKEN_TYPE)
  removeStoredValue(STORAGE_KEYS.USER_ID)
}

export const storeSessionTokens = (tokenResponse: TokenResponse) => {
  if (!tokenResponse?.access_token) {
    return
  }

  const expiresInSeconds = tokenResponse.expires_in || TOKEN_EXPIRY_FALLBACK_SECONDS
  const expiresAt = Date.now() + expiresInSeconds * MILLISECONDS_PER_SECOND

  setStoredValue(STORAGE_KEYS.ACCESS_TOKEN, tokenResponse.access_token)
  setStoredValue(STORAGE_KEYS.REFRESH_TOKEN, tokenResponse.refresh_token || EMPTY_STRING)
  setStoredValue(STORAGE_KEYS.TOKEN_TYPE, tokenResponse.token_type || BEARER_PREFIX)
  setStoredValue(STORAGE_KEYS.EXPIRES_AT, String(expiresAt))
  if (tokenResponse.user_id) {
    setStoredValue(STORAGE_KEYS.USER_ID, tokenResponse.user_id)
  }
}

export const apiRequest = async <T>(
  path: string,
  options: ApiRequestOptions = {},
): Promise<ApiResult<T>> => {
  const method = options.method ?? HTTP_METHODS.GET
  const requiresAuth = options.requiresAuth ?? false
  const headers: Record<string, string> = { ...(options.headers ?? {}) }

  if (options.body !== undefined) {
    headers[CONTENT_TYPE_HEADER] = CONTENT_TYPE_JSON
  }

  if (requiresAuth) {
    const token = getAccessToken()
    if (!token) {
      return {
        data: null,
        error: ERROR_MESSAGES.MISSING_TOKEN,
        status: null,
      }
    }
    headers[AUTH_HEADER_NAME] = `${BEARER_PREFIX} ${token}`
  }

  const controller = new AbortController()
  const timeoutId = window.setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS)

  try {
    const response = await fetch(buildUrl(path), {
      method,
      headers,
      body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
      signal: controller.signal,
    })

    const contentType = response.headers.get(CONTENT_TYPE_HEADER) ?? EMPTY_STRING
    const isJson = contentType.includes(CONTENT_TYPE_JSON)
    const responseBody = isJson ? await response.json() : await response.text()

    if (!response.ok) {
      return {
        data: null,
        error: typeof responseBody === 'string' ? responseBody : ERROR_MESSAGES.INVALID_RESPONSE,
        status: response.status,
      }
    }

    return {
      data: responseBody as T,
      error: null,
      status: response.status,
    }
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      return { data: null, error: ERROR_MESSAGES.TIMEOUT, status: null }
    }

    return { data: null, error: ERROR_MESSAGES.NETWORK, status: null }
  } finally {
    window.clearTimeout(timeoutId)
  }
}

const buildUrl = (path: string) => `${API_BASE_URL}/${path.replace(/^\/+/, EMPTY_STRING)}`

const getStoredValue = (key: string) => {
  if (typeof window === 'undefined') {
    return null
  }
  return window.localStorage.getItem(key)
}

const setStoredValue = (key: string, value: string) => {
  if (typeof window === 'undefined') {
    return
  }
  window.localStorage.setItem(key, value)
}

const removeStoredValue = (key: string) => {
  if (typeof window === 'undefined') {
    return
  }
  window.localStorage.removeItem(key)
}
