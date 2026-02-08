import { Link } from 'react-router-dom'
import { CalendarCheck, CheckCircle2, HeartPulse, Lock, ShieldCheck } from 'lucide-react'
import { API_BASE_URL } from '../lib/api'

const steps = [
  'Authorize access to your clinic Google Calendar.',
  'Check connection status and disconnect anytime.',
  'Use availability lookups when booking appointments.',
]

const CalendarConnectPage = () => {
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
                <h1 className="text-2xl font-semibold text-slate-900">Connect Google Calendar</h1>
                <p className="text-sm text-slate-600">
                  Link your clinic calendar to sync availability and appointments.
                </p>
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

            <a
              href={`${API_BASE_URL}/calendar/auth-url`}
              className="mt-8 block w-full rounded-full bg-primary px-6 py-3 text-center text-sm font-semibold text-white transition hover:bg-blue-700"
            >
              Authorize Calendar
            </a>
            <p className="mt-3 text-xs text-slate-500">
              Admin-only connection. Patients never access this portal.
            </p>
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
