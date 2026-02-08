import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiRequest, API_PATHS, HTTP, storeSessionTokens, type TokenResponse } from '../lib/api'

const PAGE_TITLE = 'Signing you in'
const PAGE_SUBTITLE = 'Completing Google authentication...'
const ERROR_TITLE = 'Unable to complete sign-in'
const REDIRECT_MESSAGE = 'Redirecting to your dashboard...'
const ERROR_GENERIC = 'Unable to complete sign-in.'
const ERROR_MISSING_CODE = 'Missing authorization code from Google callback.'

const PARAM_ACCESS_TOKEN = 'access_token'
const PARAM_REFRESH_TOKEN = 'refresh_token'
const PARAM_TOKEN_TYPE = 'token_type'
const PARAM_EXPIRES_IN = 'expires_in'
const PARAM_USER_ID = 'user_id'
const PARAM_CODE = 'code'
const PARAM_STATE = 'state'
const PARAM_ERROR = 'error'
const PARAM_ERROR_DESCRIPTION = 'error_description'

const DEFAULT_TOKEN_TYPE = 'bearer'
const DEFAULT_EXPIRES_IN = 1800
const DASHBOARD_ROUTE = '/app'

const OAuthCallbackPage = () => {
  const navigate = useNavigate()
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const hasStartedRef = useRef(false)

  useEffect(() => {
    if (hasStartedRef.current) {
      return
    }
    hasStartedRef.current = true

    const completeLogin = async () => {
      const params = new URLSearchParams(window.location.search)
      const error = params.get(PARAM_ERROR)
      const errorDescription = params.get(PARAM_ERROR_DESCRIPTION)

      if (error) {
        setErrorMessage(errorDescription ?? error)
        return
      }

      const accessToken = params.get(PARAM_ACCESS_TOKEN)
      if (accessToken) {
        const refreshToken = params.get(PARAM_REFRESH_TOKEN) ?? ''
        const tokenType = params.get(PARAM_TOKEN_TYPE) ?? DEFAULT_TOKEN_TYPE
        const expiresIn = Number(params.get(PARAM_EXPIRES_IN)) || DEFAULT_EXPIRES_IN
        const userId = params.get(PARAM_USER_ID) ?? undefined

        storeSessionTokens({
          access_token: accessToken,
          refresh_token: refreshToken,
          token_type: tokenType,
          expires_in: expiresIn,
          user_id: userId,
        })

        navigate(DASHBOARD_ROUTE, { replace: true })
        return
      }

      const code = params.get(PARAM_CODE)
      const state = params.get(PARAM_STATE)

      if (!code || !state) {
        setErrorMessage(ERROR_MISSING_CODE)
        return
      }

      const result = await apiRequest<TokenResponse>(API_PATHS.AUTH_GOOGLE_CALLBACK, {
        method: HTTP.POST,
        body: { code, state },
      })

      if (result.error || !result.data?.access_token) {
        setErrorMessage(result.error ?? ERROR_GENERIC)
        return
      }

      storeSessionTokens(result.data)
      navigate(DASHBOARD_ROUTE, { replace: true })
    }

    completeLogin().catch(() => setErrorMessage(ERROR_GENERIC))
  }, [navigate])

  return (
    <div className="min-h-screen bg-background px-6 py-12">
      <div className="mx-auto max-w-lg rounded-3xl border border-slate-200 bg-white p-8 text-center shadow-soft">
        <h1 className="text-2xl font-semibold text-slate-900">
          {errorMessage ? ERROR_TITLE : PAGE_TITLE}
        </h1>
        <p className="mt-2 text-sm text-slate-600">
          {errorMessage ? errorMessage : PAGE_SUBTITLE}
        </p>
        {!errorMessage && <p className="mt-4 text-xs text-slate-500">{REDIRECT_MESSAGE}</p>}
      </div>
    </div>
  )
}

export default OAuthCallbackPage
