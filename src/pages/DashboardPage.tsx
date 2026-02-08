import type { LucideIcon } from 'lucide-react'
import {
  AlertCircle,
  Calendar,
  CheckCircle,
  Clock,
  Phone,
  RefreshCw,
  XCircle,
} from 'lucide-react'
import StatCard from '../components/StatCard'
import StatusBadge from '../components/StatusBadge'

type StatItem = {
  title: string
  value: string
  change?: string
  icon: LucideIcon
  accent?: 'primary' | 'success' | 'warning'
}

const stats: StatItem[] = [
  {
    title: "Today's Reminder Calls",
    value: '12',
    change: '↑ 8% from yesterday',
    icon: Phone,
    accent: 'primary',
  },
  {
    title: 'Patients Confirmed',
    value: '10 (83%)',
    icon: CheckCircle,
    accent: 'success',
  },
  {
    title: 'Rescheduled',
    value: '2',
    icon: Calendar,
    accent: 'primary',
  },
  {
    title: 'Need Follow-up',
    value: '1',
    icon: AlertCircle,
    accent: 'warning',
  },
]

type CallStatus = 'Scheduled' | 'Completed' | 'Failed' | 'Rescheduled'

type StatusVariant = 'info' | 'success' | 'danger' | 'warning'

type StatusMeta = {
  label: string
  icon: LucideIcon
  variant: StatusVariant
}

type ReminderCall = {
  time: string
  patient: string
  phone: string
  status: CallStatus
  action: string
}

const reminderCalls: ReminderCall[] = [
  { time: '9:00 AM', patient: 'Mrs. Johnson, 78', phone: '555-0123', status: 'Scheduled', action: 'View' },
  { time: '11:30 AM', patient: 'Mr. Chen, 82', phone: '555-0456', status: 'Completed', action: 'Details' },
  { time: '2:00 PM', patient: 'Ms. Rodriguez, 71', phone: '555-0789', status: 'Scheduled', action: 'View' },
  { time: '3:30 PM', patient: 'Mr. Lopez, 75', phone: '555-0912', status: 'Scheduled', action: 'View' },
]

const statusConfig: Record<CallStatus, StatusMeta> = {
  Scheduled: { label: 'Scheduled', icon: Clock, variant: 'info' },
  Completed: { label: 'Completed', icon: CheckCircle, variant: 'success' },
  Failed: { label: 'Failed', icon: XCircle, variant: 'danger' },
  Rescheduled: { label: 'Rescheduled', icon: RefreshCw, variant: 'warning' },
}

const recentActivity = [
  { detail: 'Mrs. Johnson confirmed appointment', time: '5 min ago' },
  { detail: 'Mr. Chen rescheduled to Friday', time: '23 min ago' },
  { detail: 'New patient added: Ms. Rodriguez', time: '1 hour ago' },
]

const DashboardPage = () => {
  return (
    <div className="space-y-6">
      <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-4">
        {stats.map((stat) => (
          <StatCard
            key={stat.title}
            title={stat.title}
            value={stat.value}
            change={stat.change}
            icon={stat.icon}
            accent={stat.accent}
          />
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-[2fr_1fr]">
        <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-soft">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h2 className="text-lg font-semibold text-slate-900">Reminder Calls Scheduled Today</h2>
          </div>

          <div className="mt-5 overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="border-b border-slate-100 bg-slate-50 text-xs font-semibold uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-4 py-3">Time</th>
                  <th className="px-4 py-3">Patient</th>
                  <th className="px-4 py-3">Phone</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {reminderCalls.map((call) => {
                  const statusMeta = statusConfig[call.status]
                  return (
                    <tr key={`${call.time}-${call.patient}`} className="text-slate-600">
                      <td className="px-4 py-4 text-sm font-semibold text-slate-900">{call.time}</td>
                      <td className="px-4 py-4">{call.patient}</td>
                      <td className="px-4 py-4">{call.phone}</td>
                      <td className="px-4 py-4">
                        <StatusBadge
                          label={statusMeta.label}
                          variant={statusMeta.variant}
                          icon={statusMeta.icon}
                        />
                      </td>
                      <td className="px-4 py-4 text-right">
                        <button className="rounded-full border border-slate-200 px-3 py-1 text-xs font-semibold text-slate-600 transition hover:border-primary hover:text-primary">
                          {call.action}
                        </button>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </section>

        <aside className="rounded-3xl border border-slate-200 bg-white p-6 shadow-soft">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-slate-900">Recent activity</h2>
          </div>
          <ul className="relative mt-5 space-y-6 border-l border-slate-200 pl-5">
            {recentActivity.map((activity) => (
              <li key={activity.detail} className="relative">
                <span className="absolute -left-[9px] top-1 h-3.5 w-3.5 rounded-full border-2 border-white bg-primary"></span>
                <p className="text-sm font-semibold text-slate-900">{activity.detail}</p>
                <p className="text-xs text-slate-500">{activity.time}</p>
              </li>
            ))}
          </ul>
        </aside>
      </div>
    </div>
  )
}

export default DashboardPage
