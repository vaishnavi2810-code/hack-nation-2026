import { Link } from 'react-router-dom'
import { ArrowRight, HeartPulse, Lock, Mail } from 'lucide-react'

const LoginPage = () => {
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
          <h1 className="text-2xl font-semibold text-slate-900">Welcome back</h1>
          <p className="mt-2 text-sm text-slate-600">
            Sign in to manage your clinic&apos;s AI calling coverage.
          </p>

          <form className="mt-6 space-y-4">
            <label className="block text-sm font-semibold text-slate-700">
              Work email
              <div className="relative mt-2">
                <Mail className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                <input
                  type="email"
                  placeholder="doctor@clinic.com"
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 py-2.5 pl-10 pr-3 text-sm text-slate-700 outline-none transition focus:border-primary focus:bg-white"
                />
              </div>
            </label>
            <label className="block text-sm font-semibold text-slate-700">
              Password
              <div className="relative mt-2">
                <Lock className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                <input
                  type="password"
                  placeholder="••••••••"
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 py-2.5 pl-10 pr-3 text-sm text-slate-700 outline-none transition focus:border-primary focus:bg-white"
                />
              </div>
            </label>
            <Link
              to="/app"
              className="flex w-full items-center justify-center gap-2 rounded-full bg-primary px-6 py-3 text-sm font-semibold text-white transition hover:bg-blue-700"
            >
              Sign in to dashboard
              <ArrowRight className="h-4 w-4" />
            </Link>
          </form>

          <div className="mt-5 flex items-center justify-between text-xs text-slate-500">
            <span>Doctor-only access</span>
            <button className="font-semibold text-primary">Forgot password?</button>
          </div>
        </div>

        <div className="mt-6 rounded-2xl border border-dashed border-slate-300 bg-white/60 px-6 py-4 text-xs text-slate-500">
          Need onboarding?{' '}
          <Link to="/connect-calendar" className="font-semibold text-primary">
            Connect Google Calendar
          </Link>{' '}
          to activate your clinic workspace.
        </div>
      </div>
    </div>
  )
}

export default LoginPage
