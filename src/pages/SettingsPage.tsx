import { Bell, Building2, Shield, SlidersHorizontal } from 'lucide-react'

const SettingsPage = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Settings</h1>
        <p className="mt-1 text-sm text-slate-600">
          Configure clinic preferences and AI calling policies.
        </p>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-soft">
          <div className="flex items-center gap-3">
            <Building2 className="h-5 w-5 text-primary" />
            <h2 className="text-base font-semibold text-slate-900">Clinic profile</h2>
          </div>
          <p className="mt-3 text-sm text-slate-600">
            Update office hours, practice name, and caller ID displayed by MomMode.
          </p>
          <button className="mt-4 rounded-full border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-600 transition hover:border-primary hover:text-primary">
            Edit clinic profile
          </button>
        </div>

        <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-soft">
          <div className="flex items-center gap-3">
            <Bell className="h-5 w-5 text-success" />
            <h2 className="text-base font-semibold text-slate-900">Notification routing</h2>
          </div>
          <p className="mt-3 text-sm text-slate-600">
            Control which call outcomes notify staff and which remain AI-only.
          </p>
          <button className="mt-4 rounded-full border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-600 transition hover:border-primary hover:text-primary">
            Manage alerts
          </button>
        </div>

        <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-soft">
          <div className="flex items-center gap-3">
            <SlidersHorizontal className="h-5 w-5 text-warning" />
            <h2 className="text-base font-semibold text-slate-900">Call scripts</h2>
          </div>
          <p className="mt-3 text-sm text-slate-600">
            Customize intake prompts and escalation rules used by the AI caller.
          </p>
          <button className="mt-4 rounded-full border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-600 transition hover:border-primary hover:text-primary">
            Edit scripts
          </button>
        </div>

        <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-soft">
          <div className="flex items-center gap-3">
            <Shield className="h-5 w-5 text-primary" />
            <h2 className="text-base font-semibold text-slate-900">Security & access</h2>
          </div>
          <p className="mt-3 text-sm text-slate-600">
            Manage doctor-only access, audit logs, and data retention policies.
          </p>
          <button className="mt-4 rounded-full border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-600 transition hover:border-primary hover:text-primary">
            Review policies
          </button>
        </div>
      </div>
    </div>
  )
}

export default SettingsPage
