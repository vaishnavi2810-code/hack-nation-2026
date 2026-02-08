import { Eye, PhoneCall, PhoneMissed, PhoneOutgoing, Plus } from 'lucide-react'
import StatusBadge from '../components/StatusBadge'

const calls = [
  {
    id: 'call-001',
    caller: 'Hannah Lee',
    time: 'Today · 9:02 AM',
    summary: 'Confirmed annual physical for Feb 10.',
    type: 'Inbound',
    status: 'Completed',
  },
  {
    id: 'call-002',
    caller: 'Carlos Diaz',
    time: 'Today · 9:18 AM',
    summary: 'Requested to move appointment to next week.',
    type: 'Inbound',
    status: 'Escalated',
  },
  {
    id: 'call-003',
    caller: 'MomMode AI',
    time: 'Today · 10:05 AM',
    summary: 'Reminder call completed for Jordan Patel.',
    type: 'Outbound',
    status: 'Completed',
  },
  {
    id: 'call-004',
    caller: 'Maya Rivera',
    time: 'Yesterday · 4:42 PM',
    summary: 'Voicemail left, awaiting confirmation.',
    type: 'Missed',
    status: 'Follow-up',
  },
]

const notifyAction = (message: string) => {
  console.log(message)
  window.alert(message)
}

const CallHistoryPage = () => {
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Call history</h1>
          <p className="mt-1 text-sm text-slate-600">
            Review call outcomes and schedule manual follow-ups for your clinic.
          </p>
        </div>
        <button
          type="button"
          onClick={() => notifyAction('Schedule call via POST /calls/manual')}
          className="inline-flex items-center gap-2 rounded-full bg-primary px-4 py-2 text-sm font-semibold text-white transition hover:bg-blue-700"
        >
          <Plus className="h-4 w-4" />
          Schedule manual call
        </button>
      </div>

      <div className="grid gap-4">
        {calls.map((call) => {
          const icon =
            call.type === 'Outbound' ? (
              <PhoneOutgoing className="h-4 w-4 text-primary" />
            ) : call.type === 'Missed' ? (
              <PhoneMissed className="h-4 w-4 text-warning" />
            ) : (
              <PhoneCall className="h-4 w-4 text-success" />
            )

          return (
            <div
              key={call.id}
              className="flex flex-wrap items-center justify-between gap-4 rounded-3xl border border-slate-200 bg-white px-6 py-4 shadow-soft"
            >
              <div className="flex items-start gap-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-full bg-slate-100">
                  {icon}
                </div>
                <div>
                  <p className="text-sm font-semibold text-slate-900">{call.caller}</p>
                  <p className="text-xs text-slate-500">{call.summary}</p>
                </div>
              </div>
              <div className="text-sm text-slate-600">{call.time}</div>
              <div className="text-xs font-semibold text-slate-500">{call.type}</div>
              <StatusBadge
                label={call.status}
                variant={
                  call.status === 'Completed'
                    ? 'success'
                    : call.status === 'Escalated'
                      ? 'warning'
                      : 'info'
                }
              />
              <button
                type="button"
                onClick={() => notifyAction(`Fetch call via GET /calls/${call.id}`)}
                className="inline-flex items-center gap-1 text-xs font-semibold text-primary"
              >
                <Eye className="h-3.5 w-3.5" />
                View details
              </button>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default CallHistoryPage
