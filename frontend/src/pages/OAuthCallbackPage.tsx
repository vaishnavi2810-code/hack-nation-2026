import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { storeSessionTokens } from '../lib/api'

const PAGE_TITLE = 'Signing you in'
const PAGE_SUBTITLE = 'Completing Google authentication...'
const ERROR_TITLE = 'Unable to complete sign-in'
const ERROR_SUBTITLE = 'Missing access token from Google callback.'
const REDIRECT_MESSAGE = 'Redirecting to your dashboard...'

const PARAM_ACCESS_TOKEN = 'access_token'
const PARAM_REFRESH_TOKEN = 'refresh_token'
const PARAM_TOKEN_TYPE = 'token_type'
const PARAM_EXPIRES_IN = 'expires_in'
const PARAM_USER_ID = 'user_id'

const DEFAULT_TOKEN_TYPE = 'bearer'
const DEFAULT_EXPIRES_IN = 1800

const OAuthCallbackPage = () => {
  const navigate = useNavigate()
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const accessToken = params.get(PARAM_ACCESS_TOKEN)
    const refreshToken = params.get(PARAM_REFRESH_TOKEN) ?? ''
    const tokenType = params.get(PARAM_TOKEN_TYPE) ?? DEFAULT_TOKEN_TYPE
    const expiresIn = Number(params.get(PARAM_EXPIRES_IN)) || DEFAULT_EXPIRES_IN
    const userId = params.get(PARAM_USER_ID) ?? undefined

    if (!accessToken) {
      setErrorMessage(ERROR_SUBTITLE)
      return
    }

    storeSessionTokens({
      access_token: accessToken,
      refresh_token: refreshToken,
      token_type: tokenType,
      expires_in: expiresIn,
      user_id: userId,
    })

    navigate('/app', { replace: true })
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
