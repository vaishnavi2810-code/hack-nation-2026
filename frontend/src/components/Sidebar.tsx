import { useEffect, useRef, useState } from 'react'
import { NavLink } from 'react-router-dom'
import { CalendarCheck, CalendarDays, HeartPulse } from 'lucide-react'
import { apiRequest, API_PATHS, ERRORS, HTTP } from '../lib/api'

type DoctorProfile = {
  id: string
  email: string
  name: string
  phone: string
  timezone: string
  calendar_connected: boolean
  created_at: string
}

const ROUTE_APP = '/app'
const ROUTE_APPOINTMENTS = '/app/appointments'
const BRAND_NAME = 'MomMode'
const BRAND_SUBTITLE = 'Doctor Portal'
const NAV_LABEL_SUMMARY = 'Appointment summary'
const NAV_LABEL_APPOINTMENTS = 'Appointments'
const FOOTER_TITLE = 'Doctor workspace'
const FOOTER_SUBTITLE = 'Login to review appointment summaries.'
const FOOTER_LOGGED_IN_SUBTITLE = 'Signed in'
const EMPTY_STRING = ''

const navItems = [
  { label: NAV_LABEL_SUMMARY, to: ROUTE_APP, icon: CalendarDays },
  { label: NAV_LABEL_APPOINTMENTS, to: ROUTE_APPOINTMENTS, icon: CalendarCheck },
]

const Sidebar = () => {
  const [doctorEmail, setDoctorEmail] = useState<string | null>(null)
  const hasLoadedRef = useRef(false)

  useEffect(() => {
    if (hasLoadedRef.current) {
      return
    }
    hasLoadedRef.current = true

    const loadDoctorProfile = async () => {
      const result = await apiRequest<DoctorProfile>(API_PATHS.DOCTOR_PROFILE, {
        method: HTTP.GET,
        requiresAuth: true,
      })

      if (result.error) {
        if (result.error === ERRORS.MISSING_TOKEN) {
          setDoctorEmail(null)
        }
        return
      }

      const email = result.data?.email?.trim()
      if (email) {
        setDoctorEmail(email)
      }
    }

    loadDoctorProfile()
  }, [])

  const footerTitle = doctorEmail ?? FOOTER_TITLE
  const footerSubtitle = doctorEmail ? FOOTER_LOGGED_IN_SUBTITLE : FOOTER_SUBTITLE

  return (
    <aside className="flex min-h-screen w-64 flex-col border-r border-slate-200 bg-white">
      <div className="flex items-center gap-3 border-b border-slate-200 px-6 py-5">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10 text-primary">
          <HeartPulse className="h-5 w-5" />
        </div>
        <div>
          <p className="text-lg font-semibold text-slate-900">{BRAND_NAME}</p>
          <p className="text-xs text-slate-500">{BRAND_SUBTITLE}</p>
        </div>
      </div>
      <nav className="flex-1 space-y-1 px-4 py-6">
        {navItems.map((item) => {
          const Icon = item.icon
          return (
            <NavLink
              key={item.label}
              to={item.to}
              end={item.to === '/app'}
              className={({ isActive }) =>
                [
                  'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition',
                  isActive
                    ? 'bg-primary text-white shadow-sm'
                    : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900',
                ].join(' ')
              }
            >
              <Icon className="h-4 w-4" />
              {item.label}
            </NavLink>
          )
        })}
      </nav>
      <div className="border-t border-slate-200 px-6 py-4 text-xs text-slate-500">
        <p className="font-semibold text-slate-700">{footerTitle || EMPTY_STRING}</p>
        <p>{footerSubtitle}</p>
      </div>
    </aside>
  )
}

export default Sidebar
