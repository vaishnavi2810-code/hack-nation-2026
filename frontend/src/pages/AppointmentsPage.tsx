import { useEffect, useState } from 'react'
import { CalendarDays, CheckCircle2, MapPin, PencilLine, Plus, Trash2, Video } from 'lucide-react'
import StatusBadge from '../components/StatusBadge'
import { apiRequest, API_PATHS, ERRORS, HTTP } from '../lib/api'

type AppointmentRecord = {
  id: string
  patient_id: string
  patient_name: string
  date: string
  time: string
  type: string
  status: string
}

const FALLBACK_APPOINTMENTS = [
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

const STATUS_LABELS: Record<string, string> = {
  scheduled: 'Scheduled',
  confirmed: 'Confirmed',
  cancelled: 'Cancelled',
  completed: 'Completed',
  no_show: 'No show',
}

const CHANNEL_TELEHEALTH_KEYWORD = 'tele'
const STATUS_LABEL_PENDING = 'Pending'
const CHANNEL_LABEL_TELEHEALTH = 'Telehealth'
const CHANNEL_LABEL_IN_PERSON = 'In-person'

const STATUS_LOADING = 'Loading appointments...'
const STATUS_MISSING_TOKEN = 'Add access token to load appointments.'
const STATUS_LOAD_ERROR = 'Unable to load appointments.'
const STATUS_ACTION_ERROR = 'Unable to complete appointment action.'

const PROMPT_PATIENT_ID = 'Enter patient ID'
const PROMPT_DATE = 'Enter appointment date (YYYY-MM-DD)'
const PROMPT_TIME = 'Enter appointment time (HH:MM)'
const PROMPT_TYPE = 'Enter appointment type'

const DEFAULT_APPOINTMENT_TYPE = 'General Checkup'

const AppointmentsPage = () => {
  const [appointments, setAppointments] = useState(FALLBACK_APPOINTMENTS)
  const [statusMessage, setStatusMessage] = useState<string | null>(null)

  const mapAppointments = (records: AppointmentRecord[]) =>
    records.map((record) => ({
      id: record.id,
      patient: record.patient_name,
      time: `${record.date} · ${record.time}`,
      type: record.type,
      channel: record.type?.toLowerCase().includes(CHANNEL_TELEHEALTH_KEYWORD)
        ? CHANNEL_LABEL_TELEHEALTH
        : CHANNEL_LABEL_IN_PERSON,
      status: STATUS_LABELS[record.status] ?? record.status,
    }))

  const loadAppointments = async () => {
    setStatusMessage(STATUS_LOADING)
    const result = await apiRequest<AppointmentRecord[]>(API_PATHS.APPOINTMENTS, {
      method: HTTP.GET,
      requiresAuth: true,
    })

    if (result.error) {
      setStatusMessage(result.error === ERRORS.MISSING_TOKEN ? STATUS_MISSING_TOKEN : STATUS_LOAD_ERROR)
      return
    }

    if (result.data) {
      setAppointments(mapAppointments(result.data))
    }
    setStatusMessage(null)
  }

  useEffect(() => {
    loadAppointments()
  }, [])

  const handleCreateAppointment = async () => {
    const patientId = window.prompt(PROMPT_PATIENT_ID)
    if (!patientId) {
      return
    }
    const date = window.prompt(PROMPT_DATE)
    if (!date) {
      return
    }
    const time = window.prompt(PROMPT_TIME)
    if (!time) {
      return
    }
    const type = window.prompt(PROMPT_TYPE, DEFAULT_APPOINTMENT_TYPE) ?? DEFAULT_APPOINTMENT_TYPE

    const result = await apiRequest<AppointmentRecord>(API_PATHS.APPOINTMENTS, {
      method: HTTP.POST,
      requiresAuth: true,
      body: {
        patient_id: patientId,
        date,
        time,
        type,
      },
    })

    if (result.error) {
      setStatusMessage(STATUS_ACTION_ERROR)
      return
    }

    loadAppointments()
  }

  const handleConfirmAppointment = async (appointmentId: string) => {
    const result = await apiRequest(API_PATHS.APPOINTMENT_CONFIRM(appointmentId), {
      method: HTTP.POST,
      requiresAuth: true,
      body: {},
    })

    if (result.error) {
      setStatusMessage(STATUS_ACTION_ERROR)
      return
    }

    loadAppointments()
  }

  const handleUpdateAppointment = async (appointmentId: string) => {
    const date = window.prompt(PROMPT_DATE)
    const time = window.prompt(PROMPT_TIME)
    const type = window.prompt(PROMPT_TYPE)

    const result = await apiRequest(API_PATHS.APPOINTMENT_BY_ID(appointmentId), {
      method: HTTP.PUT,
      requiresAuth: true,
      body: {
        date: date || undefined,
        time: time || undefined,
        type: type || undefined,
      },
    })

    if (result.error) {
      setStatusMessage(STATUS_ACTION_ERROR)
      return
    }

    loadAppointments()
  }

  const handleDeleteAppointment = async (appointmentId: string) => {
    const result = await apiRequest(API_PATHS.APPOINTMENT_BY_ID(appointmentId), {
      method: HTTP.DELETE,
      requiresAuth: true,
    })

    if (result.error) {
      setStatusMessage(STATUS_ACTION_ERROR)
      return
    }

    loadAppointments()
  }

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
          onClick={handleCreateAppointment}
          className="inline-flex items-center gap-2 rounded-full bg-primary px-4 py-2 text-sm font-semibold text-white transition hover:bg-blue-700"
        >
          <Plus className="h-4 w-4" />
          New appointment
        </button>
      </div>

      {statusMessage && <StatusBadge label={statusMessage} variant="info" />}

      <div className="flex flex-wrap items-center gap-3 rounded-2xl border border-slate-200 bg-white px-4 py-3 shadow-soft">
        <CalendarDays className="h-4 w-4 text-slate-400" />
        <span className="text-sm font-semibold text-slate-600">Upcoming schedule</span>
      </div>

      <div className="overflow-x-auto rounded-3xl border border-slate-200 bg-white shadow-soft">
        <table className="min-w-[820px] w-full table-fixed text-left text-sm">
          <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
            <tr>
              <th className="px-6 py-4 w-[26%]">Patient</th>
              <th className="px-6 py-4 w-[18%]">Time</th>
              <th className="px-6 py-4 w-[16%]">Channel</th>
              <th className="px-6 py-4 w-[14%]">Status</th>
              <th className="px-6 py-4 w-[26%]">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {appointments.map((appointment) => {
              const ChannelIcon =
                appointment.channel === 'Video' || appointment.channel === 'Telehealth'
                  ? Video
                  : MapPin

              return (
                <tr key={appointment.id} className="hover:bg-slate-50">
                  <td className="px-6 py-4">
                    <p className="text-sm font-semibold text-slate-900">{appointment.patient}</p>
                    <p className="text-xs text-slate-500">{appointment.type}</p>
                  </td>
                  <td className="px-6 py-4 text-sm text-slate-600">{appointment.time}</td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2 text-sm text-slate-600">
                      <ChannelIcon className="h-4 w-4 text-primary" />
                      {appointment.channel}
                    </div>
                  </td>
                  <td className="px-6 py-4">
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
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex flex-wrap items-center gap-2 text-xs font-semibold">
                      {appointment.status === STATUS_LABEL_PENDING && (
                        <button
                          type="button"
                          onClick={() => handleConfirmAppointment(appointment.id)}
                          className="inline-flex items-center gap-1 rounded-full border border-emerald-200 px-3 py-1 text-emerald-600 transition hover:border-emerald-300"
                        >
                          <CheckCircle2 className="h-3.5 w-3.5" />
                          Confirm
                        </button>
                      )}
                      <button
                        type="button"
                        onClick={() => handleUpdateAppointment(appointment.id)}
                        className="inline-flex items-center gap-1 rounded-full border border-slate-200 px-3 py-1 text-slate-600 transition hover:border-primary hover:text-primary"
                      >
                        <PencilLine className="h-3.5 w-3.5" />
                        Edit
                      </button>
                      <button
                        type="button"
                        onClick={() => handleDeleteAppointment(appointment.id)}
                        className="inline-flex items-center gap-1 rounded-full border border-rose-200 px-3 py-1 text-rose-500 transition hover:border-rose-300"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                        Cancel
                      </button>
                    </div>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default AppointmentsPage
