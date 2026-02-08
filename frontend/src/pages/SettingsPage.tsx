import { Bell, Building2, CalendarDays } from 'lucide-react'
import { Link } from 'react-router-dom'

const notifyAction = (message: string) => {
  console.log(message)
  window.alert(message)
}

const SettingsPage = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Settings</h1>
        <p className="mt-1 text-sm text-slate-600">
          Update clinic settings and notification preferences.
        </p>
      </div>

      <form className="space-y-6">
        <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-soft">
          <div className="flex items-center gap-3">
            <Building2 className="h-5 w-5 text-primary" />
            <h2 className="text-base font-semibold text-slate-900">Clinic settings</h2>
          </div>
          <div className="mt-4 grid gap-4 md:grid-cols-2">
            <label className="block text-sm font-semibold text-slate-700">
              Clinic name
              <input
                type="text"
                placeholder="Summit Family Clinic"
                className="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm text-slate-700 outline-none transition focus:border-primary focus:bg-white"
              />
            </label>
            <label className="block text-sm font-semibold text-slate-700">
              Timezone
              <select
                defaultValue="America/Los_Angeles"
                className="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm text-slate-700 outline-none transition focus:border-primary focus:bg-white"
              >
                <option value="America/Los_Angeles">Pacific (US)</option>
                <option value="America/Denver">Mountain (US)</option>
                <option value="America/Chicago">Central (US)</option>
                <option value="America/New_York">Eastern (US)</option>
              </select>
            </label>
            <label className="block text-sm font-semibold text-slate-700">
              Default appointment length (minutes)
              <input
                type="number"
                min="10"
                step="5"
                placeholder="30"
                className="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm text-slate-700 outline-none transition focus:border-primary focus:bg-white"
              />
            </label>
            <label className="block text-sm font-semibold text-slate-700">
              Clinic contact phone
              <input
                type="tel"
                placeholder="(555) 555-0199"
                className="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm text-slate-700 outline-none transition focus:border-primary focus:bg-white"
              />
            </label>
          </div>
        </div>

        <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-soft">
          <div className="flex items-center gap-3">
            <Bell className="h-5 w-5 text-success" />
            <h2 className="text-base font-semibold text-slate-900">Notification preferences</h2>
          </div>
          <div className="mt-4 space-y-3 text-sm text-slate-600">
            <label className="flex items-center gap-2">
              <input type="checkbox" defaultChecked className="h-4 w-4 rounded border-slate-300" />
              Notify staff on missed calls
            </label>
            <label className="flex items-center gap-2">
              <input type="checkbox" defaultChecked className="h-4 w-4 rounded border-slate-300" />
              Notify staff on appointment reschedules
            </label>
            <label className="flex items-center gap-2">
              <input type="checkbox" className="h-4 w-4 rounded border-slate-300" />
              Send confirmation reminders for upcoming appointments
            </label>
          </div>
        </div>

        <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-soft">
          <div className="flex items-center gap-3">
            <CalendarDays className="h-5 w-5 text-primary" />
            <h2 className="text-base font-semibold text-slate-900">Calendar connection</h2>
          </div>
          <p className="mt-3 text-sm text-slate-600">
            Manage Google Calendar access to keep availability and appointments in sync.
          </p>
          <Link
            to="/connect-calendar"
            className="mt-4 inline-flex rounded-full border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-600 transition hover:border-primary hover:text-primary"
          >
            Manage calendar connection
          </Link>
        </div>

        <div className="flex justify-end">
          <button
            type="button"
            onClick={() => notifyAction('Update settings via PUT /settings')}
            className="rounded-full bg-primary px-6 py-3 text-sm font-semibold text-white transition hover:bg-blue-700"
          >
            Save settings
          </button>
        </div>
      </form>
    </div>
  )
}

export default SettingsPage
