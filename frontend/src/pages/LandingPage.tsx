import { Link } from 'react-router-dom'
import {
  ArrowRight,
  CalendarDays,
  CheckCircle2,
  HeartPulse,
  PhoneCall,
  ShieldCheck,
  Sparkles,
  Stethoscope,
  UsersRound,
} from 'lucide-react'

const stats = [
  { label: 'Average wait time', value: '18 sec' },
  { label: 'Calls handled weekly', value: '1,240+' },
  { label: 'Booking completion rate', value: '96%' },
]

const features = [
  {
    title: 'AI call coverage for small clinics',
    description: 'Handle intake, reschedules, and reminders without adding staff.',
    icon: PhoneCall,
  },
  {
    title: 'Calendar-first scheduling',
    description: 'MomMode syncs directly to Google Calendar for real-time accuracy.',
    icon: CalendarDays,
  },
  {
    title: 'Doctor-grade oversight',
    description: 'Review call summaries, appointments, and patient records in one place.',
    icon: ShieldCheck,
  },
  {
    title: 'Clinic-ready patient context',
    description: 'Surface visit history, contact details, and upcoming appointments instantly.',
    icon: UsersRound,
  },
]

const LandingPage = () => {
  return (
    <div className="min-h-screen bg-background text-slate-900">
      <header className="flex flex-wrap items-center justify-between gap-4 px-6 py-6 lg:px-12">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10 text-primary">
            <HeartPulse className="h-5 w-5" />
          </div>
          <div>
            <p className="text-lg font-semibold">MomMode</p>
            <p className="text-xs text-slate-500">AI calling system for clinics</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Link
            to="/login"
            className="rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-600 transition hover:border-primary hover:text-primary"
          >
            Doctor Login
          </Link>
          <Link
            to="/signup"
            className="rounded-full bg-primary px-5 py-2 text-sm font-semibold text-white transition hover:bg-blue-700"
          >
            Create account
          </Link>
        </div>
      </header>

      <main>
        <section className="grid gap-12 px-6 py-10 lg:grid-cols-[1.1fr_0.9fr] lg:px-12 lg:py-16">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full bg-primary/10 px-3 py-1 text-xs font-semibold text-primary">
              <Sparkles className="h-4 w-4" />
              Built for doctor-led practices
            </div>
            <h1 className="mt-5 text-4xl font-semibold leading-tight text-slate-900 lg:text-5xl">
              MomMode keeps your phone lines covered while you focus on patient care.
            </h1>
            <p className="mt-5 text-lg text-slate-600">
              Automate appointment calls, confirmations, and reminders with a clinic-ready AI
              caller. Designed for small doctor practices that need reliable coverage without
              patient-facing portals.
            </p>
            <div className="mt-8 flex flex-wrap items-center gap-4">
              <Link
                to="/signup"
                className="inline-flex items-center gap-2 rounded-full bg-primary px-6 py-3 text-sm font-semibold text-white transition hover:bg-blue-700"
              >
                Create account
                <ArrowRight className="h-4 w-4" />
              </Link>
              <Link
                to="/connect-calendar"
                className="inline-flex items-center gap-2 rounded-full border border-slate-200 px-6 py-3 text-sm font-semibold text-slate-700 transition hover:border-primary hover:text-primary"
              >
                Connect Google Calendar
              </Link>
            </div>
            <div className="mt-8 flex flex-wrap gap-6 text-sm text-slate-600">
              {stats.map((stat) => (
                <div key={stat.label}>
                  <p className="text-xl font-semibold text-slate-900">{stat.value}</p>
                  <p>{stat.label}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="space-y-4">
            <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-soft">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                    Today&apos;s clinic snapshot
                  </p>
                  <p className="mt-2 text-2xl font-semibold text-slate-900">18 calls handled</p>
                </div>
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-success/10 text-success">
                  <PhoneCall className="h-6 w-6" />
                </div>
              </div>
              <div className="mt-6 space-y-4 text-sm text-slate-600">
                {[
                  '6 appointment confirmations sent',
                  '4 reschedules routed to staff',
                  '2 follow-up calls scheduled',
                ].map((item) => (
                  <div key={item} className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-success" />
                    {item}
                  </div>
                ))}
              </div>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-soft">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10 text-primary">
                  <Stethoscope className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-sm font-semibold text-slate-900">Doctor oversight</p>
                  <p className="text-xs text-slate-500">All calls stay in your control.</p>
                </div>
              </div>
              <div className="mt-4 space-y-3 text-sm text-slate-600">
                <p>• Real-time call summaries for every appointment request.</p>
                <p>• Automatic escalation to staff for exceptions.</p>
                <p>• HIPAA-conscious workflows with secure access controls.</p>
              </div>
            </div>
          </div>
        </section>

        <section className="px-6 py-12 lg:px-12">
          <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-4">
            {features.map((feature) => {
              const Icon = feature.icon
              return (
                <div
                  key={feature.title}
                  className="rounded-2xl border border-slate-200 bg-white p-6 shadow-soft"
                >
                  <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-primary/10 text-primary">
                    <Icon className="h-5 w-5" />
                  </div>
                  <h3 className="mt-4 text-base font-semibold text-slate-900">{feature.title}</h3>
                  <p className="mt-2 text-sm text-slate-600">{feature.description}</p>
                </div>
              )
            })}
          </div>
        </section>

        <section className="px-6 pb-16 lg:px-12">
          <div className="rounded-3xl border border-slate-200 bg-white px-8 py-10 text-center shadow-soft">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-primary/10 text-primary">
              <HeartPulse className="h-6 w-6" />
            </div>
            <h2 className="mt-5 text-2xl font-semibold text-slate-900">
              Ready to bring AI call coverage to your clinic?
            </h2>
            <p className="mt-3 text-sm text-slate-600">
              Create a doctor account and connect Google Calendar in minutes.
            </p>
            <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
              <Link
                to="/login"
                className="rounded-full bg-primary px-6 py-3 text-sm font-semibold text-white transition hover:bg-blue-700"
              >
                Doctor login
              </Link>
              <Link
                to="/connect-calendar"
                className="rounded-full border border-slate-200 px-6 py-3 text-sm font-semibold text-slate-700 transition hover:border-primary hover:text-primary"
              >
                See calendar setup
              </Link>
            </div>
          </div>
        </section>
      </main>
    </div>
  )
}

export default LandingPage
