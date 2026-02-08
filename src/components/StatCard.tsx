import type { ComponentType, SVGProps } from 'react'

type StatCardProps = {
  title: string
  value: string
  change?: string
  icon: ComponentType<SVGProps<SVGSVGElement>>
  accent?: 'primary' | 'success' | 'warning'
}

const accentStyles: Record<NonNullable<StatCardProps['accent']>, string> = {
  primary: 'bg-primary/10 text-primary',
  success: 'bg-success/10 text-success',
  warning: 'bg-warning/10 text-warning',
}

const StatCard = ({ title, value, change, icon: Icon, accent = 'primary' }: StatCardProps) => {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-soft">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{title}</p>
          <p className="mt-2 text-3xl font-semibold text-slate-900">{value}</p>
        </div>
        <div className={`flex h-11 w-11 items-center justify-center rounded-xl ${accentStyles[accent]}`}>
          <Icon className="h-5 w-5" />
        </div>
      </div>
      {change ? <p className="mt-3 text-sm font-medium text-slate-500">{change}</p> : null}
    </div>
  )
}

export default StatCard
