import { useEffect, useState } from 'react'
import { CalendarDays, Clock, PhoneCall, UsersRound } from 'lucide-react'
import StatCard from '../components/StatCard'
import StatusBadge from '../components/StatusBadge'
import { apiRequest, API_PATHS, ERRORS, HTTP } from '../lib/api'

type DashboardStats = {
  total_patients: number
  total_appointments: number
  upcoming_appointments: number
  completed_appointments: number
  no_show_count: number
  total_calls_made: number
  successful_calls: number
}

type CallRecord = {
  id: string
  patient_name: string
  phone: string
  type: string
  status: string
  started_at?: string | null
  created_at?: string | null
}

type ScheduledCallsResponse = {
  count: number
  calls: CallRecord[]
}

type AppointmentRecord = {
  id: string
  patient_name: string
  date: string
  time: string
  type: string
  status: string
}

type UpcomingAppointmentsResponse = {
  count: number
  appointments: AppointmentRecord[]
}

type DashboardActivity = {
  recent_appointments: AppointmentRecord[]
  recent_calls: CallRecord[]
  upcoming_events: AppointmentRecord[]
}

const FALLBACK_SCHEDULED_CALLS = [
  { caller: 'Lydia Green', reason: 'Appointment confirmation', time: '11:00 AM', status: 'Scheduled' },
  { caller: 'Carlos Diaz', reason: 'Reschedule request', time: '12:30 PM', status: 'In progress' },
  { caller: 'Amanda Wu', reason: 'Reminder call', time: '3:15 PM', status: 'Scheduled' },
]

const FALLBACK_UPCOMING_APPOINTMENTS = [
  { patient: 'Hannah Lee', time: '11:30 AM', type: 'Annual physical', status: 'Confirmed' },
  { patient: 'Jordan Patel', time: '1:00 PM', type: 'Follow-up visit', status: 'Pending' },
  { patient: 'Maya Rivera', time: '2:15 PM', type: 'Telehealth check-in', status: 'Confirmed' },
]

const FALLBACK_RECENT_ACTIVITY = [
  { title: 'Appointment confirmed', detail: 'Jordan Patel · Follow-up visit', time: '10 min ago' },
  { title: 'Patient record created', detail: 'Maya Rivera · New intake', time: '1 hour ago' },
  { title: 'Call completed', detail: 'Hannah Lee · Reminder call', time: '2 hours ago' },
]

const STATUS_LOADING = 'Loading live dashboard metrics...'
const STATUS_MISSING_TOKEN = 'Add access token to load protected data.'
const STATUS_LOAD_ERROR = 'Unable to load live dashboard data.'
const EMPTY_TIME_LABEL = 'TBD'
const FALLBACK_NO_SHOW_COUNT = '0'

const formatTimestamp = (value?: string | null) => {
  if (!value) {
    return EMPTY_TIME_LABEL
  }
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) {
    return EMPTY_TIME_LABEL
  }
  return parsed.toLocaleString()
}

const DashboardPage = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [scheduledCalls, setScheduledCalls] = useState(FALLBACK_SCHEDULED_CALLS)
  const [upcomingAppointments, setUpcomingAppointments] = useState(FALLBACK_UPCOMING_APPOINTMENTS)
  const [recentActivity, setRecentActivity] = useState(FALLBACK_RECENT_ACTIVITY)
  const [statusMessage, setStatusMessage] = useState<string | null>(null)

  const mapScheduledCalls = (calls: CallRecord[]) =>
    calls.map((call) => ({
      caller: call.patient_name || call.phone,
      reason: call.type,
      time: formatTimestamp(call.started_at ?? call.created_at),
      status: call.status,
    }))

  const mapUpcomingAppointments = (appointments: AppointmentRecord[]) =>
    appointments.map((appointment) => ({
      patient: appointment.patient_name,
      time: `${appointment.date} · ${appointment.time}`,
      type: appointment.type,
      status: appointment.status,
    }))

  const mapRecentActivity = (activity: DashboardActivity) => {
    const appointmentActivities = activity.recent_appointments.map((appointment) => ({
      title: 'Appointment updated',
      detail: `${appointment.patient_name} · ${appointment.type}`,
      time: `${appointment.date} ${appointment.time}`,
    }))
    const callActivities = activity.recent_calls.map((call) => ({
      title: 'Call completed',
      detail: `${call.patient_name} · ${call.type}`,
      time: formatTimestamp(call.started_at ?? call.created_at),
    }))
    return [...appointmentActivities, ...callActivities].slice(0, FALLBACK_RECENT_ACTIVITY.length)
  }

  useEffect(() => {
    const loadDashboard = async () => {
      setStatusMessage(STATUS_LOADING)

      const [statsResult, scheduledCallsResult, upcomingResult, activityResult] = await Promise.all([
        apiRequest<DashboardStats>(API_PATHS.DASHBOARD_STATS, { method: HTTP.GET }),
        apiRequest<ScheduledCallsResponse>(API_PATHS.CALLS_SCHEDULED, { method: HTTP.GET }),
        apiRequest<UpcomingAppointmentsResponse>(API_PATHS.APPOINTMENTS_UPCOMING, {
          method: HTTP.GET,
          requiresAuth: true,
        }),
        apiRequest<DashboardActivity>(API_PATHS.DASHBOARD_ACTIVITY, { method: HTTP.GET }),
      ])

      if (statsResult.data) {
        setStats(statsResult.data)
      }

      if (scheduledCallsResult.data?.calls) {
        setScheduledCalls(mapScheduledCalls(scheduledCallsResult.data.calls))
      }

      if (upcomingResult.data?.appointments) {
        setUpcomingAppointments(mapUpcomingAppointments(upcomingResult.data.appointments))
      } else if (upcomingResult.error === ERRORS.MISSING_TOKEN) {
        setStatusMessage(STATUS_MISSING_TOKEN)
      }

      if (activityResult.data) {
        const mappedActivity = mapRecentActivity(activityResult.data)
        if (mappedActivity.length > 0) {
          setRecentActivity(mappedActivity)
        }
      }

      if (statsResult.error || scheduledCallsResult.error || activityResult.error) {
        setStatusMessage(STATUS_LOAD_ERROR)
        return
      }

      if (!upcomingResult.error) {
        setStatusMessage(null)
      }
    }

    loadDashboard()
  }, [])

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Clinic dashboard</h1>
        <p className="mt-1 text-sm text-slate-600">
          Monitor today&apos;s call coverage, appointments, and patient touchpoints.
        </p>
        {statusMessage && (
          <div className="mt-4">
            <StatusBadge label={statusMessage} variant="info" />
          </div>
        )}
      </div>

      <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
        <StatCard
          title="Calls handled"
          value={stats ? String(stats.total_calls_made) : '128'}
          change="+12% from yesterday"
          icon={PhoneCall}
          accent="primary"
        />
        <StatCard
          title="Upcoming appointments"
          value={stats ? String(stats.upcoming_appointments) : '24'}
          change="6 need confirmations"
          icon={CalendarDays}
          accent="success"
        />
        <StatCard
          title="Active patients"
          value={stats ? String(stats.total_patients) : '128'}
          change="12 added this month"
          icon={UsersRound}
          accent="warning"
        />
        <StatCard
          title="No-show count"
          value={stats ? String(stats.no_show_count) : FALLBACK_NO_SHOW_COUNT}
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
