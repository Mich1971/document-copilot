import { Loader2 } from 'lucide-react'

interface LoaderProps {
  variant?: 'default' | 'text-shimmer'
  text?: string
  className?: string
}

export function Loader({ variant = 'default', text = 'Loading…', className = '' }: LoaderProps) {
  if (variant === 'text-shimmer') {
    return (
      <div className={`flex flex-col items-center justify-center gap-3 ${className}`}>
        <div className="relative flex items-center justify-center">
          <div className="absolute h-8 w-8 rounded-full border-2 border-primary/20" />
          <Loader2 className="h-6 w-6 animate-spin text-primary" />
        </div>
        <p className="text-sm font-medium text-muted-foreground animate-pulse tracking-wide shimmer">
          {text}
        </p>
      </div>
    )
  }

  return (
    <div className={`flex items-center justify-center gap-2 ${className}`}>
      <Loader2 className="h-5 w-5 animate-spin text-primary" />
      {text && <span className="text-sm text-muted-foreground">{text}</span>}
    </div>
  )
}
