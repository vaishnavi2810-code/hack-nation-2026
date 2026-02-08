import { CalendarDays, Clock, PhoneCall, UsersRound } from 'lucide-react'
import StatCard from '../components/StatCard'
import StatusBadge from '../components/StatusBadge'

const scheduledCalls = [
  { caller: 'Lydia Green', reason: 'Appointment confirmation', time: '11:00 AM', status: 'Scheduled' },
  { caller: 'Carlos Diaz', reason: 'Reschedule request', time: '12:30 PM', status: 'In progress' },
  { caller: 'Amanda Wu', reason: 'Reminder call', time: '3:15 PM', status: 'Scheduled' },
]

const upcomingAppointments = [
  { patient: 'Hannah Lee', time: '11:30 AM', type: 'Annual physical', status: 'Confirmed' },
  { patient: 'Jordan Patel', time: '1:00 PM', type: 'Follow-up visit', status: 'Pending' },
  { patient: 'Maya Rivera', time: '2:15 PM', type: 'Telehealth check-in', status: 'Confirmed' },
]

const recentActivity = [
  { title: 'Appointment confirmed', detail: 'Jordan Patel · Follow-up visit', time: '10 min ago' },
  { title: 'Patient record created', detail: 'Maya Rivera · New intake', time: '1 hour ago' },
  { title: 'Call completed', detail: 'Hannah Lee · Reminder call', time: '2 hours ago' },
]

const DashboardPage = () => {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Clinic dashboard</h1>
        <p className="mt-1 text-sm text-slate-600">
          Monitor today&apos;s call coverage, appointments, and patient touchpoints.
        </p>
      </div>

      <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
        <StatCard
          title="Calls handled"
          value="128"
          change="+12% from yesterday"
          icon={PhoneCall}
          accent="primary"
        />
        <StatCard
          title="Upcoming appointments"
          value="24"
          change="6 need confirmations"
          icon={CalendarDays}
          accent="success"
        />
        <StatCard
          title="Active patients"
          value="128"
          change="12 added this month"
          icon={UsersRound}
          accent="warning"
        />
        <StatCard
          title="Average call time"
          value="2m 14s"
          change="AI coverage running smoothly"
          icon={Clock}
          accent="primary"
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-soft">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-slate-900">Scheduled calls</h2>
              <p className="text-sm text-slate-600">Upcoming automated and manual calls.</p>
            </div>
            <StatusBadge label="3 scheduled" variant="info" />
          </div>
          <div className="mt-6 space-y-4">
            {scheduledCalls.map((call) => (
              <div
                key={call.caller}
                className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-slate-100 bg-slate-50 px-4 py-3"
              >
                <div>
                  <p className="text-sm font-semibold text-slate-900">{call.caller}</p>
                  <p className="text-xs text-slate-500">{call.reason}</p>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-xs text-slate-500">{call.time}</span>
                  <StatusBadge
                    label={call.status}
                    variant={
                      call.status === 'Completed'
                        ? 'success'
                        : call.status === 'In progress'
                          ? 'warning'
                          : 'info'
                    }
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="space-y-6">
          <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-soft">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-slate-900">Upcoming appointments</h2>
              <StatusBadge label="Today" variant="neutral" />
            </div>
            <div className="mt-5 space-y-4">
              {upcomingAppointments.map((appointment) => (
                <div key={appointment.patient} className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-semibold text-slate-900">{appointment.patient}</p>
                    <p className="text-xs text-slate-500">{appointment.type}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-semibold text-slate-900">{appointment.time}</p>
                    <StatusBadge
                      label={appointment.status}
                      variant={appointment.status === 'Confirmed' ? 'success' : 'warning'}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-soft">
            <div className="flex items-center justify-between">
              <h2 className="text-base font-semibold text-slate-900">Recent activity</h2>
              <StatusBadge label="Last 24 hours" variant="neutral" />
            </div>
            <div className="mt-4 space-y-4 text-sm text-slate-600">
              {recentActivity.map((activity) => (
                <div key={activity.title} className="flex items-center justify-between gap-3">
                  <div>
                    <p className="text-sm font-semibold text-slate-900">{activity.title}</p>
                    <p className="text-xs text-slate-500">{activity.detail}</p>
                  </div>
                  <span className="text-xs text-slate-500">{activity.time}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default DashboardPage
