import { useCallback, useEffect, useMemo, useState } from 'react'
import type { ComponentType, SVGProps } from 'react'
import { AlertTriangle, CalendarDays, CheckCircle2, ClipboardList } from 'lucide-react'
import StatCard from '../components/StatCard'
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

type AppointmentRow = {
  id: string
  patient: string
  dateTime: string
  type: string
  status: string
}

type SummaryCounts = {
  total: number
  upcoming: number
  completed: number
  needsAttention: number
}

type SummaryKey = keyof SummaryCounts

type StatusVariant = 'success' | 'warning' | 'info' | 'neutral'

type SummaryCardConfig = {
  key: SummaryKey
  title: string
  note: string
  icon: ComponentType<SVGProps<SVGSVGElement>>
  accent: 'primary' | 'success' | 'warning'
}

const PAGE_TITLE = 'Appointment summary'
const PAGE_SUBTITLE = 'Review upcoming visits and appointment status at a glance.'
const STATUS_LOADING = 'Loading appointment summary...'
const STATUS_MISSING_TOKEN = 'Add access token to load appointment summary.'
const STATUS_LOAD_ERROR = 'Unable to load appointment summary.'
const REFRESH_LABEL = 'Refresh summary'
const REFRESHING_LABEL = 'Refreshing...'
const QUERY_SEPARATOR = '?'
const QUERY_KEY_VALUE_SEPARATOR = '='
const CALENDAR_DATE_QUERY_PARAM = 'date'
const CALENDAR_DATE_TODAY = 'today'

const UPCOMING_SECTION_TITLE = 'Upcoming appointments'
const UPCOMING_SECTION_SUBTITLE = 'Next scheduled visits for your clinic.'
const UPCOMING_EMPTY_TITLE = 'No upcoming appointments'
const UPCOMING_EMPTY_MESSAGE = 'New appointments will appear once scheduled.'

const COLUMN_PATIENT = 'Patient'
const COLUMN_TIME = 'Date & time'
const COLUMN_TYPE = 'Type'
const COLUMN_STATUS = 'Status'

const STATUS_SCHEDULED = 'scheduled'
const STATUS_CONFIRMED = 'confirmed'
const STATUS_COMPLETED = 'completed'
const STATUS_CANCELLED = 'cancelled'
const STATUS_NO_SHOW = 'no_show'

const UPCOMING_STATUSES = new Set([STATUS_SCHEDULED, STATUS_CONFIRMED])
const NEEDS_ATTENTION_STATUSES = new Set([STATUS_CANCELLED, STATUS_NO_SHOW])

const STATUS_LABELS: Record<string, string> = {
  [STATUS_SCHEDULED]: 'Scheduled',
  [STATUS_CONFIRMED]: 'Confirmed',
  [STATUS_COMPLETED]: 'Completed',
  [STATUS_CANCELLED]: 'Cancelled',
  [STATUS_NO_SHOW]: 'No show',
}

const VARIANT_INFO: StatusVariant = 'info'
const VARIANT_NEUTRAL: StatusVariant = 'neutral'
const VARIANT_SUCCESS: StatusVariant = 'success'
const VARIANT_WARNING: StatusVariant = 'warning'

const STATUS_VARIANTS: Record<string, StatusVariant> = {
  [STATUS_SCHEDULED]: VARIANT_INFO,
  [STATUS_CONFIRMED]: VARIANT_SUCCESS,
  [STATUS_COMPLETED]: VARIANT_SUCCESS,
  [STATUS_CANCELLED]: VARIANT_WARNING,
  [STATUS_NO_SHOW]: VARIANT_WARNING,
}

const DEFAULT_STATUS_VARIANT: StatusVariant = VARIANT_NEUTRAL
const UNKNOWN_STATUS_LABEL = 'Unknown status'

const DATE_TIME_SEPARATOR = ' · '
const DATE_TIME_PARSE_SEPARATOR = 'T'
const FALLBACK_DATE_TIME_LABEL = 'TBD'
const DEFAULT_APPOINTMENT_TYPE = 'General'
const DEFAULT_PATIENT_LABEL = 'Unknown patient'

const UPCOMING_LIST_LIMIT = 6
const UPCOMING_BADGE_SUFFIX = 'upcoming'

const SUMMARY_TOTAL_TITLE = 'Total appointments'
const SUMMARY_TOTAL_NOTE = 'All appointments on record.'
const SUMMARY_UPCOMING_TITLE = 'Upcoming'
const SUMMARY_UPCOMING_NOTE = 'Scheduled or confirmed visits ahead.'
const SUMMARY_COMPLETED_TITLE = 'Completed'
const SUMMARY_COMPLETED_NOTE = 'Visits already concluded.'
const SUMMARY_ATTENTION_TITLE = 'Needs attention'
const SUMMARY_ATTENTION_NOTE = 'Cancellations or no-shows.'

const SUMMARY_CARDS: SummaryCardConfig[] = [
  {
    key: 'total',
    title: SUMMARY_TOTAL_TITLE,
    note: SUMMARY_TOTAL_NOTE,
    icon: ClipboardList,
    accent: 'primary',
  },
  {
    key: 'upcoming',
    title: SUMMARY_UPCOMING_TITLE,
    note: SUMMARY_UPCOMING_NOTE,
    icon: CalendarDays,
    accent: 'success',
  },
  {
    key: 'completed',
    title: SUMMARY_COMPLETED_TITLE,
    note: SUMMARY_COMPLETED_NOTE,
    icon: CheckCircle2,
    accent: 'primary',
  },
  {
    key: 'needsAttention',
    title: SUMMARY_ATTENTION_TITLE,
    note: SUMMARY_ATTENTION_NOTE,
    icon: AlertTriangle,
    accent: 'warning',
  },
]

const INVALID_TIMESTAMP_FALLBACK = Number.POSITIVE_INFINITY

const formatAppointmentDateTime = (appointment: AppointmentRecord) => {
  if (!appointment.date || !appointment.time) {
    return FALLBACK_DATE_TIME_LABEL
  }

  return `${appointment.date}${DATE_TIME_SEPARATOR}${appointment.time}`
}

const getAppointmentTimestamp = (appointment: AppointmentRecord) => {
  if (!appointment.date || !appointment.time) {
    return null
  }

  const parsed = new Date(`${appointment.date}${DATE_TIME_PARSE_SEPARATOR}${appointment.time}`)
  if (Number.isNaN(parsed.getTime())) {
    return null
  }
  return parsed.getTime()
}

const buildAppointmentRow = (appointment: AppointmentRecord): AppointmentRow => ({
  id: appointment.id,
  patient: appointment.patient_name || DEFAULT_PATIENT_LABEL,
  dateTime: formatAppointmentDateTime(appointment),
  type: appointment.type || DEFAULT_APPOINTMENT_TYPE,
  status: appointment.status,
})

const getStatusLabel = (status: string) => STATUS_LABELS[status] ?? status ?? UNKNOWN_STATUS_LABEL

const getStatusVariant = (status: string) => STATUS_VARIANTS[status] ?? DEFAULT_STATUS_VARIANT

const formatUpcomingBadge = (count: number) => `${count} ${UPCOMING_BADGE_SUFFIX}`

const CALENDAR_APPOINTMENTS_PATH = `${API_PATHS.CALENDAR_APPOINTMENTS}${QUERY_SEPARATOR}${CALENDAR_DATE_QUERY_PARAM}${QUERY_KEY_VALUE_SEPARATOR}${CALENDAR_DATE_TODAY}`

const AppointmentSummaryPage = () => {
  const [appointments, setAppointments] = useState<AppointmentRecord[]>([])
  const [statusMessage, setStatusMessage] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  const loadAppointments = useCallback(async () => {
    setIsLoading(true)
    setStatusMessage(STATUS_LOADING)
    const result = await apiRequest<AppointmentRecord[]>(CALENDAR_APPOINTMENTS_PATH, {
      method: HTTP.GET,
      requiresAuth: true,
    })
    setIsLoading(false)

    if (result.error) {
      setAppointments([])
      setStatusMessage(result.error === ERRORS.MISSING_TOKEN ? STATUS_MISSING_TOKEN : STATUS_LOAD_ERROR)
      return
    }

    setAppointments(result.data ?? [])
    setStatusMessage(null)
  }, [])

  useEffect(() => {
    loadAppointments()
  }, [loadAppointments])

  const summaryCounts = useMemo<SummaryCounts>(() => {
    const counts: SummaryCounts = {
      total: appointments.length,
      upcoming: 0,
      completed: 0,
      needsAttention: 0,
    }

    for (const appointment of appointments) {
      if (UPCOMING_STATUSES.has(appointment.status)) {
        counts.upcoming += 1
      }
      if (appointment.status === STATUS_COMPLETED) {
        counts.completed += 1
      }
      if (NEEDS_ATTENTION_STATUSES.has(appointment.status)) {
        counts.needsAttention += 1
      }
    }

    return counts
  }, [appointments])

  const upcomingRows = useMemo(() => {
    const upcoming = appointments.filter((appointment) => UPCOMING_STATUSES.has(appointment.status))
    const sorted = [...upcoming].sort((first, second) => {
      const firstTimestamp = getAppointmentTimestamp(first) ?? INVALID_TIMESTAMP_FALLBACK
      const secondTimestamp = getAppointmentTimestamp(second) ?? INVALID_TIMESTAMP_FALLBACK
      return firstTimestamp - secondTimestamp
    })

    return sorted.slice(0, UPCOMING_LIST_LIMIT).map(buildAppointmentRow)
  }, [appointments])

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">{PAGE_TITLE}</h1>
          <p className="mt-1 text-sm text-slate-600">{PAGE_SUBTITLE}</p>
        </div>
        <button
          type="button"
          onClick={loadAppointments}
          className="inline-flex items-center rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-600 transition hover:border-primary hover:text-primary disabled:cursor-not-allowed disabled:opacity-70"
          disabled={isLoading}
        >
          {isLoading ? REFRESHING_LABEL : REFRESH_LABEL}
        </button>
      </div>

      {statusMessage && <StatusBadge label={statusMessage} variant={VARIANT_INFO} />}

      <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
        {SUMMARY_CARDS.map((card) => (
          <StatCard
            key={card.key}
            title={card.title}
            value={String(summaryCounts[card.key])}
            change={card.note}
            icon={card.icon}
            accent={card.accent}
          />
        ))}
      </div>

      <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-soft">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">{UPCOMING_SECTION_TITLE}</h2>
            <p className="mt-1 text-sm text-slate-600">{UPCOMING_SECTION_SUBTITLE}</p>
          </div>
          <StatusBadge label={formatUpcomingBadge(upcomingRows.length)} variant={VARIANT_NEUTRAL} />
        </div>

        <div className="mt-5">
          {upcomingRows.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-5 py-4">
              <p className="text-sm font-semibold text-slate-700">{UPCOMING_EMPTY_TITLE}</p>
              <p className="mt-1 text-xs text-slate-500">{UPCOMING_EMPTY_MESSAGE}</p>
            </div>
          ) : (
            <div className="overflow-x-auto rounded-2xl border border-slate-100">
              <table className="min-w-[640px] w-full table-fixed text-left text-sm">
                <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                  <tr>
                    <th className="px-5 py-3 w-[28%]">{COLUMN_PATIENT}</th>
                    <th className="px-5 py-3 w-[24%]">{COLUMN_TIME}</th>
                    <th className="px-5 py-3 w-[26%]">{COLUMN_TYPE}</th>
                    <th className="px-5 py-3 w-[22%]">{COLUMN_STATUS}</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {upcomingRows.map((appointment) => (
                    <tr key={appointment.id} className="hover:bg-slate-50">
                      <td className="px-5 py-4">
                        <p className="text-sm font-semibold text-slate-900">{appointment.patient}</p>
                      </td>
                      <td className="px-5 py-4 text-sm text-slate-600">{appointment.dateTime}</td>
                      <td className="px-5 py-4 text-sm text-slate-600">{appointment.type}</td>
                      <td className="px-5 py-4">
                        <StatusBadge
                          label={getStatusLabel(appointment.status)}
                          variant={getStatusVariant(appointment.status)}
                        />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default AppointmentSummaryPage
