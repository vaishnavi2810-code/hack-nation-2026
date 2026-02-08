import { useState } from 'react'
import { LogOut, Search } from 'lucide-react'
import { Outlet, useNavigate } from 'react-router-dom'
import Sidebar from '../components/Sidebar'
import { apiRequest, API_PATHS, clearSessionTokens, HTTP } from '../lib/api'

const AppLayout = () => {
  const [isSigningOut, setIsSigningOut] = useState(false)
  const navigate = useNavigate()

  const LOGOUT_ERROR_MESSAGE = 'Unable to log out.'
  const LABEL_SIGN_OUT = 'Sign out'
  const LABEL_SIGNING_OUT = 'Signing out'

  const handleSignOut = async () => {
    setIsSigningOut(true)
    const result = await apiRequest<{ success: boolean }>(API_PATHS.AUTH_LOGOUT, {
      method: HTTP.POST,
      requiresAuth: true,
      body: {},
    })
    setIsSigningOut(false)

    if (result.error) {
      console.error(LOGOUT_ERROR_MESSAGE, result.error)
    }

    clearSessionTokens()
    navigate('/login')
  }

  return (
    <div className="min-h-screen bg-background text-slate-900">
      <div className="flex">
        <Sidebar />
        <div className="flex min-h-screen flex-1 flex-col">
          <header className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 bg-white px-6 py-4">
            <div>
              <p className="text-sm font-semibold text-slate-900">Welcome back</p>
              <p className="text-xs text-slate-500">Clinic operations overview for today.</p>
            </div>
            <div className="flex flex-1 items-center justify-end gap-3">
              <div className="relative w-full max-w-xs">
                <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                <input
                  type="search"
                  placeholder="Search patients, appointments, or calls"
                  className="w-full rounded-full border border-slate-200 bg-slate-50 py-2 pl-9 pr-3 text-sm text-slate-700 outline-none transition focus:border-primary focus:bg-white"
                />
              </div>
              <button
                type="button"
                onClick={handleSignOut}
                className="inline-flex items-center gap-2 rounded-full border border-slate-200 px-3 py-2 text-xs font-semibold text-slate-600 transition hover:border-primary hover:text-primary disabled:cursor-not-allowed disabled:opacity-70"
                disabled={isSigningOut}
              >
                <LogOut className="h-4 w-4" />
                {isSigningOut ? LABEL_SIGNING_OUT : LABEL_SIGN_OUT}
              </button>
            </div>
          </header>
          <main className="flex-1 px-6 py-6 lg:px-10 lg:py-8">
            <Outlet />
          </main>
        </div>
      </div>
    </div>
  )
}

export default AppLayout
