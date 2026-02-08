import { PhoneCall, PhoneMissed, PhoneOutgoing } from 'lucide-react'
import StatusBadge from '../components/StatusBadge'

const calls = [
  {
    caller: 'Hannah Lee',
    time: 'Today · 9:02 AM',
    summary: 'Confirmed annual physical for Feb 10.',
    type: 'Inbound',
    status: 'Completed',
  },
  {
    caller: 'Carlos Diaz',
    time: 'Today · 9:18 AM',
    summary: 'Requested to move appointment to next week.',
    type: 'Inbound',
    status: 'Escalated',
  },
  {
    caller: 'MomMode AI',
    time: 'Today · 10:05 AM',
    summary: 'Reminder call completed for Jordan Patel.',
    type: 'Outbound',
    status: 'Completed',
  },
  {
    caller: 'Maya Rivera',
    time: 'Yesterday · 4:42 PM',
    summary: 'Voicemail left, awaiting confirmation.',
    type: 'Missed',
    status: 'Follow-up',
  },
]

const CallHistoryPage = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Call history</h1>
        <p className="mt-1 text-sm text-slate-600">
          Review AI call outcomes and staff escalations for your clinic.
        </p>
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
              key={`${call.caller}-${call.time}`}
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
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default CallHistoryPage
