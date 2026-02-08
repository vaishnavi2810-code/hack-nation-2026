import { CalendarDays, Filter, MapPin, Plus, Video } from 'lucide-react'
import StatusBadge from '../components/StatusBadge'

const appointments = [
  {
    patient: 'Hannah Lee',
    time: 'Today · 11:30 AM',
    type: 'Annual physical',
    channel: 'In-person',
    status: 'Confirmed',
  },
  {
    patient: 'Jordan Patel',
    time: 'Today · 1:00 PM',
    type: 'Follow-up',
    channel: 'Telehealth',
    status: 'Pending',
  },
  {
    patient: 'Maya Rivera',
    time: 'Today · 2:15 PM',
    type: 'Telehealth check-in',
    channel: 'Video',
    status: 'Confirmed',
  },
  {
    patient: 'Carlos Diaz',
    time: 'Tomorrow · 9:00 AM',
    type: 'Rescheduled visit',
    channel: 'In-person',
    status: 'Needs review',
  },
]

const AppointmentsPage = () => {
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Appointments</h1>
          <p className="mt-1 text-sm text-slate-600">
            Monitor bookings synced to Google Calendar and AI call confirmations.
          </p>
        </div>
        <button className="inline-flex items-center gap-2 rounded-full bg-primary px-4 py-2 text-sm font-semibold text-white transition hover:bg-blue-700">
          <Plus className="h-4 w-4" />
          New appointment
        </button>
      </div>

      <div className="flex flex-wrap items-center gap-3 rounded-2xl border border-slate-200 bg-white px-4 py-3 shadow-soft">
        <CalendarDays className="h-4 w-4 text-slate-400" />
        <span className="text-sm font-semibold text-slate-600">Upcoming schedule</span>
        <div className="ml-auto flex items-center gap-2 text-xs text-slate-500">
          <Filter className="h-3.5 w-3.5" />
          Filters: Today, Confirmed, Pending
        </div>
      </div>

      <div className="grid gap-4">
        {appointments.map((appointment) => {
          const ChannelIcon =
            appointment.channel === 'Video' || appointment.channel === 'Telehealth'
              ? Video
              : MapPin

          return (
            <div
              key={`${appointment.patient}-${appointment.time}`}
              className="flex flex-wrap items-center justify-between gap-4 rounded-3xl border border-slate-200 bg-white px-6 py-4 shadow-soft"
            >
              <div>
                <p className="text-sm font-semibold text-slate-900">{appointment.patient}</p>
                <p className="text-xs text-slate-500">{appointment.type}</p>
              </div>
              <div className="text-sm text-slate-600">{appointment.time}</div>
              <div className="flex items-center gap-2 text-sm text-slate-600">
                <ChannelIcon className="h-4 w-4 text-primary" />
                {appointment.channel}
              </div>
              <StatusBadge
                label={appointment.status}
                variant={
                  appointment.status === 'Confirmed'
                    ? 'success'
                    : appointment.status === 'Pending'
                      ? 'warning'
                      : 'info'
                }
              />
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default AppointmentsPage
