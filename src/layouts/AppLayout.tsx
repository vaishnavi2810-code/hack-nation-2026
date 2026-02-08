import { Bell, Search } from 'lucide-react'
import { Outlet } from 'react-router-dom'
import Sidebar from '../components/Sidebar'

const AppLayout = () => {
  return (
    <div className="min-h-screen bg-background text-slate-900">
      <div className="flex">
        <Sidebar />
        <div className="flex min-h-screen flex-1 flex-col">
          <header className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 bg-white px-6 py-4">
            <div>
              <p className="text-sm font-semibold text-slate-900">Welcome back, Dr. Morgan</p>
              <p className="text-xs text-slate-500">Clinic operations overview for today.</p>
            </div>
            <div className="flex flex-1 items-center justify-end gap-3">
              <div className="relative w-full max-w-xs">
                <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                <input
                  type="search"
                  placeholder="Search patients or calls"
                  className="w-full rounded-full border border-slate-200 bg-slate-50 py-2 pl-9 pr-3 text-sm text-slate-700 outline-none transition focus:border-primary focus:bg-white"
                />
              </div>
              <button className="flex h-9 w-9 items-center justify-center rounded-full border border-slate-200 text-slate-500 transition hover:border-primary hover:text-primary">
                <Bell className="h-4 w-4" />
              </button>
              <div className="flex items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-semibold text-slate-600">
                <span className="h-2 w-2 rounded-full bg-success"></span>
                Live
              </div>
            </div>
          </header>
          <main className="flex-1 px-6 py-6 lg:px-10 lg:py-8">
            <Outlet />
          </main>
        </div>
      </div>
    </div>
  )
}

export default AppLayout
