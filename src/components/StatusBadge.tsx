import type { ComponentType, SVGProps } from 'react'

type StatusBadgeProps = {
  label: string
  variant?: 'success' | 'warning' | 'info' | 'neutral' | 'danger'
  icon?: ComponentType<SVGProps<SVGSVGElement>>
}

const variantStyles: Record<NonNullable<StatusBadgeProps['variant']>, string> = {
  success: 'bg-success/10 text-success',
  warning: 'bg-warning/10 text-warning',
  info: 'bg-primary/10 text-primary',
  neutral: 'bg-slate-100 text-slate-600',
  danger: 'bg-danger/10 text-danger',
}

const StatusBadge = ({ label, variant = 'neutral', icon: Icon }: StatusBadgeProps) => {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold ${variantStyles[variant]}`}
    >
      {Icon ? <Icon className="h-3.5 w-3.5" /> : null}
      {label}
    </span>
  )
}

export default StatusBadge
