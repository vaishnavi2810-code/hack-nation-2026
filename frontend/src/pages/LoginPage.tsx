import { useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowRight, HeartPulse } from 'lucide-react'
import { apiRequest, API_PATHS, HTTP } from '../lib/api'

const LoginPage = () => {
  const [isLoading, setIsLoading] = useState(false)

  const BUTTON_LABEL = 'Continue with Google'
  const BUTTON_LOADING_LABEL = 'Redirecting...'
  const AUTH_ERROR_MESSAGE = 'Unable to start Google sign-in.'
  const PAGE_TITLE = 'Doctor login'
  const PAGE_SUBTITLE = 'Use your Google account to access appointment summaries.'
  const SUPPORT_TEXT = 'Google login is required for secure doctor access.'
  const ACCESS_NOTE_TITLE = 'Doctor-only access'
  const ACCESS_NOTE_BODY = 'Contact your clinic administrator if you need a login.'

  const handleGoogleSignIn = async () => {
    setIsLoading(true)
    const result = await apiRequest<{ auth_url: string }>(API_PATHS.AUTH_GOOGLE_URL, {
      method: HTTP.GET,
    })
    setIsLoading(false)

    if (result.error || !result.data?.auth_url) {
      console.error(AUTH_ERROR_MESSAGE, result.error)
      return
    }

    window.location.assign(result.data.auth_url)
  }

  return (
    <div className="min-h-screen bg-background px-6 py-12">
      <div className="mx-auto max-w-md">
        <Link to="/" className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10 text-primary">
            <HeartPulse className="h-5 w-5" />
          </div>
          <div>
            <p className="text-lg font-semibold text-slate-900">MomMode</p>
            <p className="text-xs text-slate-500">Doctor portal access</p>
          </div>
        </Link>

        <div className="mt-8 rounded-3xl border border-slate-200 bg-white p-8 shadow-soft">
          <h1 className="text-2xl font-semibold text-slate-900">{PAGE_TITLE}</h1>
          <p className="mt-2 text-sm text-slate-600">{PAGE_SUBTITLE}</p>

          <div className="mt-6 space-y-4">
            <button
              type="button"
              onClick={handleGoogleSignIn}
              className="flex w-full items-center justify-center gap-2 rounded-full bg-primary px-6 py-3 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-70"
              disabled={isLoading}
            >
              {isLoading ? BUTTON_LOADING_LABEL : BUTTON_LABEL}
              <ArrowRight className="h-4 w-4" />
            </button>
            <p className="text-xs text-slate-500">{SUPPORT_TEXT}</p>
          </div>
        </div>

        <div className="mt-6 rounded-2xl border border-dashed border-slate-300 bg-white/60 px-6 py-4 text-xs text-slate-500">
          <p className="font-semibold text-slate-700">{ACCESS_NOTE_TITLE}</p>
          <p className="mt-1">{ACCESS_NOTE_BODY}</p>
        </div>
      </div>
    </div>
  )
}

export default LoginPage
