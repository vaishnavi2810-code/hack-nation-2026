import StatusBadge from '../components/StatusBadge'

type BadgeVariant = 'success' | 'warning' | 'info' | 'neutral'

type BadgeConfig = {
  label: string
  variant: BadgeVariant
}

const API_METHODS = {
  GET: 'GET',
  POST: 'POST',
  PUT: 'PUT',
  DELETE: 'DELETE',
} as const

type ApiMethod = (typeof API_METHODS)[keyof typeof API_METHODS]

type ApiEndpoint = {
  id: string
  method: ApiMethod
  path: string
  auth: BadgeConfig
  status: BadgeConfig
}

type ApiSection = {
  id: string
  title: string
  description: string
  badge: BadgeConfig
  endpoints: ApiEndpoint[]
}

const PAGE_TITLE = 'API reference'
const PAGE_SUBTITLE = 'All callable backend endpoints exposed to the frontend.'

const SECTION_AUTH_TITLE = 'JWT required endpoints'
const SECTION_AUTH_DESCRIPTION = 'Send Authorization: Bearer <token> with these calls.'

const SECTION_PUBLIC_TITLE = 'Public endpoints in current backend code'
const SECTION_PUBLIC_DESCRIPTION = 'These routes do not enforce JWT authentication.'

const TABLE_HEADERS = {
  METHOD: 'Method',
  PATH: 'Path',
  AUTH: 'Auth',
  STATUS: 'Status',
}

const METHOD_BADGE_BASE_CLASS =
  'inline-flex items-center justify-center rounded-full px-3 py-1 text-xs font-semibold'

const METHOD_BADGE_STYLES: Record<ApiMethod, string> = {
  GET: 'bg-slate-100 text-slate-700',
  POST: 'bg-primary/10 text-primary',
  PUT: 'bg-warning/10 text-warning',
  DELETE: 'bg-red-100 text-red-600',
}

const PATH_CLASSNAME =
  'inline-flex w-full rounded-lg bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-700'

const LABEL_PUBLIC = 'Public'
const LABEL_JWT_REQUIRED = 'JWT required'
const LABEL_IMPLEMENTED = 'Implemented'
const LABEL_STUBBED = 'Stubbed'
const LABEL_EXTERNAL = 'External dependency'

const AUTH_BADGES = {
  PUBLIC: { label: LABEL_PUBLIC, variant: 'neutral' as const },
  JWT_REQUIRED: { label: LABEL_JWT_REQUIRED, variant: 'info' as const },
}

const STATUS_BADGES = {
  IMPLEMENTED: { label: LABEL_IMPLEMENTED, variant: 'success' as const },
  STUBBED: { label: LABEL_STUBBED, variant: 'warning' as const },
  EXTERNAL: { label: LABEL_EXTERNAL, variant: 'info' as const },
}

const API_SECTIONS: ApiSection[] = [
  {
    id: 'auth-required',
    title: SECTION_AUTH_TITLE,
    description: SECTION_AUTH_DESCRIPTION,
    badge: AUTH_BADGES.JWT_REQUIRED,
    endpoints: [
      {
        id: 'auth-logout',
        method: API_METHODS.POST,
        path: '/api/auth/logout',
        auth: AUTH_BADGES.JWT_REQUIRED,
        status: STATUS_BADGES.STUBBED,
      },
      {
        id: 'calendar-status',
        method: API_METHODS.GET,
        path: '/api/calendar/status',
        auth: AUTH_BADGES.JWT_REQUIRED,
        status: STATUS_BADGES.IMPLEMENTED,
      },
      {
        id: 'calendar-disconnect',
        method: API_METHODS.POST,
        path: '/api/calendar/disconnect',
        auth: AUTH_BADGES.JWT_REQUIRED,
        status: STATUS_BADGES.IMPLEMENTED,
      },
      {
        id: 'calendar-check-availability',
        method: API_METHODS.POST,
        path: '/api/calendar/check-availability',
        auth: AUTH_BADGES.JWT_REQUIRED,
        status: STATUS_BADGES.IMPLEMENTED,
      },
      {
        id: 'appointments-list',
        method: API_METHODS.GET,
        path: '/api/appointments',
        auth: AUTH_BADGES.JWT_REQUIRED,
        status: STATUS_BADGES.IMPLEMENTED,
      },
      {
        id: 'appointments-upcoming',
        method: API_METHODS.GET,
        path: '/api/appointments/upcoming',
        auth: AUTH_BADGES.JWT_REQUIRED,
        status: STATUS_BADGES.IMPLEMENTED,
      },
      {
        id: 'appointments-create',
        method: API_METHODS.POST,
        path: '/api/appointments',
        auth: AUTH_BADGES.JWT_REQUIRED,
        status: STATUS_BADGES.IMPLEMENTED,
      },
    ],
  },
  {
    id: 'public',
    title: SECTION_PUBLIC_TITLE,
    description: SECTION_PUBLIC_DESCRIPTION,
    badge: AUTH_BADGES.PUBLIC,
    endpoints: [
      {
        id: 'health',
        method: API_METHODS.GET,
        path: '/health',
        auth: AUTH_BADGES.PUBLIC,
        status: STATUS_BADGES.IMPLEMENTED,
      },
      {
        id: 'auth-google-url',
        method: API_METHODS.GET,
        path: '/api/auth/google/url',
        auth: AUTH_BADGES.PUBLIC,
        status: STATUS_BADGES.EXTERNAL,
      },
      {
        id: 'auth-google-callback',
        method: API_METHODS.POST,
        path: '/api/auth/google/callback',
        auth: AUTH_BADGES.PUBLIC,
        status: STATUS_BADGES.EXTERNAL,
      },
      {
        id: 'doctors-me',
        method: API_METHODS.GET,
        path: '/api/doctors/me',
        auth: AUTH_BADGES.PUBLIC,
        status: STATUS_BADGES.STUBBED,
      },
      {
        id: 'patients-list',
        method: API_METHODS.GET,
        path: '/api/patients',
        auth: AUTH_BADGES.PUBLIC,
        status: STATUS_BADGES.STUBBED,
      },
      {
        id: 'patients-create',
        method: API_METHODS.POST,
        path: '/api/patients',
        auth: AUTH_BADGES.PUBLIC,
        status: STATUS_BADGES.STUBBED,
      },
      {
        id: 'patients-get',
        method: API_METHODS.GET,
        path: '/api/patients/{patient_id}',
        auth: AUTH_BADGES.PUBLIC,
        status: STATUS_BADGES.STUBBED,
      },
      {
        id: 'patients-update',
        method: API_METHODS.PUT,
        path: '/api/patients/{patient_id}',
        auth: AUTH_BADGES.PUBLIC,
        status: STATUS_BADGES.STUBBED,
      },
      {
        id: 'patients-delete',
        method: API_METHODS.DELETE,
        path: '/api/patients/{patient_id}',
        auth: AUTH_BADGES.PUBLIC,
        status: STATUS_BADGES.STUBBED,
      },
      {
        id: 'appointments-update',
        method: API_METHODS.PUT,
        path: '/api/appointments/{appointment_id}',
        auth: AUTH_BADGES.PUBLIC,
        status: STATUS_BADGES.STUBBED,
      },
      {
        id: 'appointments-delete',
        method: API_METHODS.DELETE,
        path: '/api/appointments/{appointment_id}',
        auth: AUTH_BADGES.PUBLIC,
        status: STATUS_BADGES.STUBBED,
      },
      {
        id: 'appointments-confirm',
        method: API_METHODS.POST,
        path: '/api/appointments/{appointment_id}/confirm',
        auth: AUTH_BADGES.PUBLIC,
        status: STATUS_BADGES.STUBBED,
      },
      {
        id: 'calls-list',
        method: API_METHODS.GET,
        path: '/api/calls',
        auth: AUTH_BADGES.PUBLIC,
        status: STATUS_BADGES.STUBBED,
      },
      {
        id: 'calls-scheduled',
        method: API_METHODS.GET,
        path: '/api/calls/scheduled',
        auth: AUTH_BADGES.PUBLIC,
        status: STATUS_BADGES.STUBBED,
      },
      {
        id: 'calls-get',
        method: API_METHODS.GET,
        path: '/api/calls/{call_id}',
        auth: AUTH_BADGES.PUBLIC,
        status: STATUS_BADGES.STUBBED,
      },
      {
        id: 'calls-manual',
        method: API_METHODS.POST,
        path: '/api/calls/manual',
        auth: AUTH_BADGES.PUBLIC,
        status: STATUS_BADGES.STUBBED,
      },
      {
        id: 'dashboard-stats',
        method: API_METHODS.GET,
        path: '/api/dashboard/stats',
        auth: AUTH_BADGES.PUBLIC,
        status: STATUS_BADGES.STUBBED,
      },
      {
        id: 'dashboard-activity',
        method: API_METHODS.GET,
        path: '/api/dashboard/activity',
        auth: AUTH_BADGES.PUBLIC,
        status: STATUS_BADGES.STUBBED,
      },
      {
        id: 'settings-get',
        method: API_METHODS.GET,
        path: '/api/settings',
        auth: AUTH_BADGES.PUBLIC,
        status: STATUS_BADGES.IMPLEMENTED,
      },
      {
        id: 'settings-update',
        method: API_METHODS.PUT,
        path: '/api/settings',
        auth: AUTH_BADGES.PUBLIC,
        status: STATUS_BADGES.STUBBED,
      },
    ],
  },
]

const ApiReferencePage = () => {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">{PAGE_TITLE}</h1>
        <p className="mt-1 text-sm text-slate-600">{PAGE_SUBTITLE}</p>
      </div>

      <div className="space-y-6">
        {API_SECTIONS.map((section) => (
          <section key={section.id} className="rounded-3xl border border-slate-200 bg-white p-6 shadow-soft">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <h2 className="text-base font-semibold text-slate-900">{section.title}</h2>
                <p className="mt-1 text-sm text-slate-600">{section.description}</p>
              </div>
              <StatusBadge label={section.badge.label} variant={section.badge.variant} />
            </div>

            <div className="mt-5 overflow-hidden rounded-2xl border border-slate-100">
              <div className="grid grid-cols-[auto_1fr_auto_auto] gap-3 border-b border-slate-100 bg-slate-50 px-4 py-3 text-xs font-semibold uppercase tracking-wide text-slate-500">
                <span>{TABLE_HEADERS.METHOD}</span>
                <span>{TABLE_HEADERS.PATH}</span>
                <span>{TABLE_HEADERS.AUTH}</span>
                <span>{TABLE_HEADERS.STATUS}</span>
              </div>
              <div className="divide-y divide-slate-100">
                {section.endpoints.map((endpoint) => (
                  <div
                    key={endpoint.id}
                    className="grid grid-cols-[auto_1fr_auto_auto] items-center gap-3 px-4 py-4"
                  >
                    <span className={`${METHOD_BADGE_BASE_CLASS} ${METHOD_BADGE_STYLES[endpoint.method]}`}>
                      {endpoint.method}
                    </span>
                    <code className={PATH_CLASSNAME}>{endpoint.path}</code>
                    <StatusBadge label={endpoint.auth.label} variant={endpoint.auth.variant} />
                    <StatusBadge label={endpoint.status.label} variant={endpoint.status.variant} />
                  </div>
                ))}
              </div>
            </div>
          </section>
        ))}
      </div>
    </div>
  )
}

export default ApiReferencePage
