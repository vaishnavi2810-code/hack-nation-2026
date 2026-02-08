import { CalendarDays, CheckCircle2, MapPin, PencilLine, Plus, Trash2, Video } from 'lucide-react'
import StatusBadge from '../components/StatusBadge'

const appointments = [
  {
    id: 'apt-001',
    patient: 'Hannah Lee',
    time: 'Today · 11:30 AM',
    type: 'Annual physical',
    channel: 'In-person',
    status: 'Confirmed',
  },
  {
    id: 'apt-002',
    patient: 'Jordan Patel',
    time: 'Today · 1:00 PM',
    type: 'Follow-up',
    channel: 'Telehealth',
    status: 'Pending',
  },
  {
    id: 'apt-003',
    patient: 'Maya Rivera',
    time: 'Today · 2:15 PM',
    type: 'Telehealth check-in',
    channel: 'Video',
    status: 'Confirmed',
  },
  {
    id: 'apt-004',
    patient: 'Carlos Diaz',
    time: 'Tomorrow · 9:00 AM',
    type: 'Rescheduled visit',
    channel: 'In-person',
    status: 'Needs review',
  },
]

const notifyAction = (message: string) => {
  console.log(message)
  window.alert(message)
}

const AppointmentsPage = () => {
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Appointments</h1>
          <p className="mt-1 text-sm text-slate-600">
            Manage bookings, confirmations, and reschedules synced to Google Calendar.
          </p>
        </div>
        <button
          type="button"
          onClick={() => notifyAction('Create appointment via POST /appointments')}
          className="inline-flex items-center gap-2 rounded-full bg-primary px-4 py-2 text-sm font-semibold text-white transition hover:bg-blue-700"
        >
          <Plus className="h-4 w-4" />
          New appointment
        </button>
      </div>

      <div className="flex flex-wrap items-center gap-3 rounded-2xl border border-slate-200 bg-white px-4 py-3 shadow-soft">
        <CalendarDays className="h-4 w-4 text-slate-400" />
        <span className="text-sm font-semibold text-slate-600">Upcoming schedule</span>
      </div>

      <div className="grid gap-4">
        {appointments.map((appointment) => {
          const ChannelIcon =
            appointment.channel === 'Video' || appointment.channel === 'Telehealth'
              ? Video
              : MapPin

          return (
            <div
              key={appointment.id}
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
              <div className="flex flex-wrap items-center gap-2 text-xs font-semibold">
                {appointment.status === 'Pending' && (
                  <button
                    type="button"
                    onClick={() =>
                      notifyAction(`Confirm appointment via POST /appointments/${appointment.id}/confirm`)
                    }
                    className="inline-flex items-center gap-1 rounded-full border border-emerald-200 px-3 py-1 text-emerald-600 transition hover:border-emerald-300"
                  >
                    <CheckCircle2 className="h-3.5 w-3.5" />
                    Confirm
                  </button>
                )}
                <button
                  type="button"
                  onClick={() =>
                    notifyAction(`Update appointment via PUT /appointments/${appointment.id}`)
                  }
                  className="inline-flex items-center gap-1 rounded-full border border-slate-200 px-3 py-1 text-slate-600 transition hover:border-primary hover:text-primary"
                >
                  <PencilLine className="h-3.5 w-3.5" />
                  Edit
                </button>
                <button
                  type="button"
                  onClick={() =>
                    notifyAction(`Cancel appointment via DELETE /appointments/${appointment.id}`)
                  }
                  className="inline-flex items-center gap-1 rounded-full border border-rose-200 px-3 py-1 text-rose-500 transition hover:border-rose-300"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                  Cancel
                </button>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default AppointmentsPage
