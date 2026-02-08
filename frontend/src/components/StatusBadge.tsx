type StatusBadgeProps = {
  label: string
  variant?: 'success' | 'warning' | 'info' | 'neutral'
}

const variantStyles: Record<NonNullable<StatusBadgeProps['variant']>, string> = {
  success: 'bg-success/10 text-success',
  warning: 'bg-warning/10 text-warning',
  info: 'bg-primary/10 text-primary',
  neutral: 'bg-slate-100 text-slate-600',
}

const StatusBadge = ({ label, variant = 'neutral' }: StatusBadgeProps) => {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold ${variantStyles[variant]}`}
    >
      {label}
    </span>
  )
}

export default StatusBadge
