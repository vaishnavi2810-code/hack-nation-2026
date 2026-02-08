import { useEffect, useState, type FormEvent, type ReactNode } from 'react'
import { Link } from 'react-router-dom'
import {
  Calendar,
  CalendarCheck,
  CheckCircle2,
  HeartPulse,
  Loader2,
  PhoneCall,
  UserPlus,
} from 'lucide-react'

const steps = [
  { id: 1, label: 'Basic Info' },
  { id: 2, label: 'Connect Google Calendar' },
  { id: 3, label: 'Quick Tutorial' },
]

type StepPanelProps = {
  isActive: boolean
  children: ReactNode
}

const StepPanel = ({ isActive, children }: StepPanelProps) => (
  <div
    className={`absolute inset-0 transition-all duration-500 ease-in-out ${
      isActive ? 'opacity-100 translate-y-0' : 'pointer-events-none opacity-0 translate-y-4'
    }`}
    aria-hidden={!isActive}
  >
    {children}
  </div>
)

type TooltipBubbleProps = {
  label: string
  className: string
  arrowClassName: string
}

const TooltipBubble = ({ label, className, arrowClassName }: TooltipBubbleProps) => (
  <div
    className={`pointer-events-none absolute z-10 rounded-xl bg-slate-900 px-3 py-2 text-xs text-white shadow-lg ${className}`}
  >
    {label}
    <span
      className={`absolute h-2 w-2 rotate-45 bg-slate-900 ${arrowClassName}`}
      aria-hidden="true"
    />
  </div>
)

const DoctorOnboardingPage = () => {
  const [step, setStep] = useState(1)
  const [isConnecting, setIsConnecting] = useState(false)
  const [isConnected, setIsConnected] = useState(false)

  useEffect(() => {
    if (!isConnecting) {
      return
    }

    const timer = window.setTimeout(() => {
      setIsConnecting(false)
      setIsConnected(true)
    }, 2000)

    return () => window.clearTimeout(timer)
  }, [isConnecting])

  useEffect(() => {
    if (step !== 2) {
      setIsConnecting(false)
      setIsConnected(false)
    }
  }, [step])

  const progress = Math.round((step / steps.length) * 100)

  const handleNext = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!event.currentTarget.checkValidity()) {
      event.currentTarget.reportValidity()
      return
    }
    setStep(2)
  }

  const handleConnect = () => {
    if (isConnecting || isConnected) {
      return
    }
    setIsConnecting(true)
  }

  return (
    <div className="min-h-screen bg-background px-6 py-12">
      <div className="mx-auto max-w-4xl">
        <Link to="/" className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10 text-primary">
            <HeartPulse className="h-5 w-5" />
          </div>
          <div>
            <p className="text-lg font-semibold text-slate-900">MomMode</p>
            <p className="text-xs text-slate-500">Doctor onboarding</p>
          </div>
        </Link>

        <div className="mt-8 rounded-3xl border border-slate-200 bg-white p-6 shadow-soft">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <p className="text-sm font-semibold text-slate-900">
                Step {step} of {steps.length}
              </p>
              <p className="text-xs text-slate-500">{steps[step - 1].label}</p>
            </div>
            <div className="flex items-center gap-2 text-xs text-slate-500">
              {steps.map((entry) => (
                <div key={entry.id} className="flex items-center gap-2">
                  <span
                    className={`h-2 w-2 rounded-full ${
                      step >= entry.id ? 'bg-primary' : 'bg-slate-200'
                    }`}
                  />
                  <span className={step === entry.id ? 'font-semibold text-slate-900' : ''}>
                    {entry.id}
                  </span>
                </div>
              ))}
            </div>
          </div>
          <div className="mt-4 h-2 w-full rounded-full bg-slate-100">
            <div
              className="h-2 rounded-full bg-primary transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        <div className="relative mt-8 min-h-[620px]">
          <StepPanel isActive={step === 1}>
            <form
              className="rounded-3xl border border-slate-200 bg-white p-8 shadow-soft"
              onSubmit={handleNext}
            >
              <h1 className="text-2xl font-semibold text-slate-900">Basic Info</h1>
              <p className="mt-2 text-sm text-slate-600">
                Tell us about your clinic so we can personalize onboarding.
              </p>

              <div className="mt-6 grid gap-4 md:grid-cols-2">
                <label className="block text-sm font-semibold text-slate-700">
                  Clinic name
                  <input
                    required
                    type="text"
                    placeholder="Summit Family Clinic"
                    className="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm text-slate-700 outline-none transition focus:border-primary focus:bg-white"
                  />
                </label>
                <label className="block text-sm font-semibold text-slate-700">
                  Doctor name
                  <input
                    required
                    type="text"
                    placeholder="Dr. Maya Rivera"
                    className="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm text-slate-700 outline-none transition focus:border-primary focus:bg-white"
                  />
                </label>
                <label className="block text-sm font-semibold text-slate-700">
                  Email
                  <input
                    required
                    type="email"
                    placeholder="doctor@clinic.com"
                    className="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm text-slate-700 outline-none transition focus:border-primary focus:bg-white"
                  />
                </label>
                <label className="block text-sm font-semibold text-slate-700">
                  Phone
                  <input
                    required
                    type="tel"
                    placeholder="(555) 555-0199"
                    className="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm text-slate-700 outline-none transition focus:border-primary focus:bg-white"
                  />
                </label>
                <label className="block text-sm font-semibold text-slate-700 md:col-span-2">
                  Specialty
                  <select
                    required
                    defaultValue=""
                    className="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm text-slate-700 outline-none transition focus:border-primary focus:bg-white"
                  >
                    <option value="" disabled>
                      Select a specialty
                    </option>
                    <option value="family-medicine">Family Medicine</option>
                    <option value="internal-medicine">Internal Medicine</option>
                    <option value="pediatrics">Pediatrics</option>
                    <option value="other">Other</option>
                  </select>
                </label>
              </div>

              <div className="mt-8 flex items-center justify-between gap-4">
                <p className="text-xs text-slate-500">
                  Required fields help us configure your intake workflow.
                </p>
                <button
                  type="submit"
                  className="rounded-full bg-primary px-6 py-3 text-sm font-semibold text-white transition hover:bg-blue-700"
                >
                  Next
                </button>
              </div>
            </form>
          </StepPanel>

          <StepPanel isActive={step === 2}>
            <div className="rounded-3xl border border-slate-200 bg-white p-8 shadow-soft">
              <div className="flex items-start gap-4">
                <div
                  className={`flex h-12 w-12 items-center justify-center rounded-2xl ${
                    isConnected ? 'bg-success/10 text-success' : 'bg-primary/10 text-primary'
                  }`}
                >
                  {isConnected ? (
                    <CheckCircle2 className="h-5 w-5" />
                  ) : (
                    <Calendar className="h-5 w-5" />
                  )}
                </div>
                <div>
                  <h2 className="text-2xl font-semibold text-slate-900">Sync Your Availability</h2>
                  <p className="mt-1 text-sm text-slate-600">
                    We&apos;ll read your Google Calendar to know when you&apos;re available for
                    appointments
                  </p>
                </div>
              </div>

              <div className="mt-6 rounded-2xl border border-slate-100 bg-slate-50 p-4">
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                  What we access
                </p>
                <ul className="mt-3 space-y-2 text-sm text-slate-600">
                  <li className="flex items-center gap-2">
                    <span className="h-1.5 w-1.5 rounded-full bg-primary" />
                    View your calendar events
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="h-1.5 w-1.5 rounded-full bg-primary" />
                    Detect free time slots
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="h-1.5 w-1.5 rounded-full bg-primary" />
                    Create reminder task events
                  </li>
                </ul>
              </div>

              <div className="mt-6 flex flex-wrap items-center gap-4">
                {!isConnected ? (
                  <button
                    type="button"
                    onClick={handleConnect}
                    disabled={isConnecting}
                    className="flex items-center gap-2 rounded-full bg-primary px-6 py-3 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-blue-300"
                  >
                    {isConnecting ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Calendar className="h-4 w-4" />
                    )}
                    {isConnecting ? 'Connecting...' : 'Connect Google Calendar'}
                  </button>
                ) : (
                  <button
                    type="button"
                    onClick={() => setStep(3)}
                    className="rounded-full bg-primary px-6 py-3 text-sm font-semibold text-white transition hover:bg-blue-700"
                  >
                    Continue to Dashboard
                  </button>
                )}

                {!isConnected && (
                  <button
                    type="button"
                    onClick={() => setStep(3)}
                    className="text-xs font-semibold text-slate-500 transition hover:text-primary"
                  >
                    I&apos;ll do this later
                  </button>
                )}
              </div>

              {isConnected && (
                <div className="mt-4 flex items-center gap-2 text-sm font-semibold text-success">
                  <CheckCircle2 className="h-4 w-4" />
                  Calendar connected!
                </div>
              )}
            </div>
          </StepPanel>

          <StepPanel isActive={step === 3}>
            <div className="space-y-6">
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div>
                  <h2 className="text-2xl font-semibold text-slate-900">Quick Tutorial</h2>
                  <p className="mt-1 text-sm text-slate-600">
                    Get oriented with a fast dashboard walkthrough.
                  </p>
                </div>
                <span className="rounded-full border border-slate-200 px-3 py-1 text-xs font-semibold text-slate-500">
                  Optional
                </span>
              </div>

              <div className="relative rounded-3xl border border-slate-200 bg-white p-6 shadow-soft">
                <div className="flex flex-wrap items-center justify-between gap-4">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                      Dashboard preview
                    </p>
                    <p className="mt-2 text-lg font-semibold text-slate-900">
                      Welcome to your clinic workspace
                    </p>
                  </div>
                  <div className="relative">
                    <button
                      type="button"
                      className="flex items-center gap-2 rounded-full bg-primary px-4 py-2 text-xs font-semibold text-white"
                    >
                      <UserPlus className="h-4 w-4" />
                      Add patient
                    </button>
                    <TooltipBubble
                      label="Add your first patient here"
                      className="right-0 top-12 w-44"
                      arrowClassName="-top-1 right-6"
                    />
                  </div>
                </div>

                <div className="mt-6 grid gap-4 md:grid-cols-2">
                  <div className="relative rounded-2xl border border-slate-100 bg-slate-50 p-4">
                    <div className="flex items-center gap-2 text-sm font-semibold text-slate-900">
                      <CalendarCheck className="h-4 w-4 text-success" />
                      Appointments
                    </div>
                    <p className="mt-2 text-xs text-slate-500">
                      Fresh availability updates from your calendar.
                    </p>
                    <TooltipBubble
                      label="Your appointments sync automatically"
                      className="-top-12 left-4 w-52"
                      arrowClassName="-bottom-1 left-6"
                    />
                  </div>
                  <div className="relative rounded-2xl border border-slate-100 bg-slate-50 p-4">
                    <div className="flex items-center gap-2 text-sm font-semibold text-slate-900">
                      <PhoneCall className="h-4 w-4 text-primary" />
                      Call outcomes
                    </div>
                    <p className="mt-2 text-xs text-slate-500">
                      Track every call result in one place.
                    </p>
                    <TooltipBubble
                      label="See all call outcomes here"
                      className="-top-12 right-4 w-44"
                      arrowClassName="-bottom-1 right-6"
                    />
                  </div>
                </div>
              </div>

              <div className="flex justify-end">
                <Link
                  to="/app"
                  className="rounded-full bg-primary px-6 py-3 text-sm font-semibold text-white transition hover:bg-blue-700"
                >
                  Got it!
                </Link>
              </div>
            </div>
          </StepPanel>
        </div>
      </div>
    </div>
  )
}

export default DoctorOnboardingPage
