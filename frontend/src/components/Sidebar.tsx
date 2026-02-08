import { NavLink } from 'react-router-dom'
import { CalendarDays, HeartPulse } from 'lucide-react'

const ROUTE_APP = '/app'
const BRAND_NAME = 'MomMode'
const BRAND_SUBTITLE = 'Doctor Portal'
const NAV_LABEL_SUMMARY = 'Appointment summary'
const FOOTER_TITLE = 'Doctor workspace'
const FOOTER_SUBTITLE = 'Login to review appointment summaries.'

const navItems = [{ label: NAV_LABEL_SUMMARY, to: ROUTE_APP, icon: CalendarDays }]

const Sidebar = () => {
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
        <p className="font-semibold text-slate-700">{FOOTER_TITLE}</p>
        <p>{FOOTER_SUBTITLE}</p>
      </div>
    </aside>
  )
}

export default Sidebar
