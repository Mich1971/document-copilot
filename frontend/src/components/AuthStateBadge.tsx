type AuthStateBadgeProps = {
  label: string
  tone?: 'default' | 'success' | 'error'
}

export function AuthStateBadge({ label, tone = 'default' }: AuthStateBadgeProps) {
  const toneClassName = {
    default: 'border-border/70 bg-muted text-muted-foreground',
    success: 'border-emerald-500/20 bg-emerald-500/10 text-emerald-700 dark:text-emerald-400',
    error: 'border-destructive/20 bg-destructive/10 text-destructive',
  }[tone]

  return (
    <span className={`inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-medium ${toneClassName}`}>
      {label}
    </span>
  )
}
