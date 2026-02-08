import { NavLink } from 'react-router-dom'
import {
  CalendarDays,
  HeartPulse,
  LayoutDashboard,
  PhoneCall,
  Settings,
  UsersRound,
} from 'lucide-react'

const navItems = [
  { label: 'Dashboard', to: '/app', icon: LayoutDashboard },
  { label: 'My Patients', to: '/app/patients', icon: UsersRound },
  { label: 'Appointments', to: '/app/appointments', icon: CalendarDays },
  { label: 'Call History', to: '/app/calls', icon: PhoneCall },
  { label: 'Settings', to: '/app/settings', icon: Settings },
]

const Sidebar = () => {
  return (
    <aside className="flex min-h-screen w-64 flex-col border-r border-slate-200 bg-white">
      <div className="flex items-center gap-3 border-b border-slate-200 px-6 py-5">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10 text-primary">
          <HeartPulse className="h-5 w-5" />
        </div>
        <div>
          <p className="text-lg font-semibold text-slate-900">MomMode</p>
          <p className="text-xs text-slate-500">Doctor Portal</p>
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
        <p className="font-semibold text-slate-700">Secure clinic workspace</p>
        <p>Doctor-only workflows, no patient-facing access.</p>
      </div>
    </aside>
  )
}

export default Sidebar
