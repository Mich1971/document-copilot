import { Link } from 'react-router-dom'
import { AlertCircle } from 'lucide-react'
import { classifyChatError } from '@/lib/chat-errors'

interface ChatErrorProps {
  error: unknown
}

export function ChatError({ error }: ChatErrorProps) {
  const classified = classifyChatError(error)

  return (
    <div className="flex gap-3 items-start bg-destructive/10 text-destructive border border-destructive/20 rounded-2xl p-4 my-2 text-sm leading-normal animate-in fade-in slide-in-from-top-1 duration-200">
      <AlertCircle className="h-5 w-5 shrink-0 mt-0.5" />
      <div className="flex-1 min-w-0 space-y-1">
        <h4 className="font-semibold text-foreground">{classified.title}</h4>
        <p className="text-muted-foreground">{classified.message}</p>
        {classified.showLoginLink && (
          <Link
            to="/login"
            className="inline-block mt-2 font-medium underline underline-offset-4 hover:text-foreground"
          >
            Sign in again
          </Link>
        )}
      </div>
    </div>
  )
}
