import { useMemo, useRef, useEffect } from 'react'
import { Message } from './Message'
import type { UIMessage, ChatStatus } from 'ai'
import type { PipelineStatus, CitationPayload } from '@/lib/citations'
import { Loader2 } from 'lucide-react'

interface MessageListProps {
  messages: UIMessage[]
  status?: ChatStatus
  pipelineStatus?: PipelineStatus | null
  onSelectCitation?: (citation: CitationPayload | null) => void
  onSendSuggestion?: (text: string) => void
}

export function MessageList({
  messages,
  status = 'ready',
  pipelineStatus = null,
  onSelectCitation,
}: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null)

  const visibleMessages = useMemo(() => {
    const filtered = messages.filter((m) => m.role !== 'system')
    if (process.env.NODE_ENV !== 'production') {
      console.log('[MessageList diag] messages=', messages.map((m) => ({ id: m.id, role: m.role, parts: (m as any).parts })))
      console.log('[MessageList diag] visibleMessages=', filtered.map((m) => ({ id: m.id, role: m.role, parts: (m as any).parts })))
      console.log('[MessageList diag] status=', status, 'pipelineStatus=', pipelineStatus)
    }
    return filtered
  }, [messages, status, pipelineStatus])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [visibleMessages, pipelineStatus])

  if (visibleMessages.length === 0 && status === 'ready') {
    return (
      <div className="flex flex-1 flex-col items-center justify-center text-center text-muted-foreground p-8">
        <svg
          className="h-12 w-12 mb-4 opacity-40 text-primary animate-pulse"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth={1.5}
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
        </svg>
        <p className="text-lg font-medium text-foreground">Inicia una conversación</p>
        <p className="text-sm mt-1 max-w-sm">
          Pregunta sobre los archivos SEC. Las citas aparecerán aquí.
        </p>
      </div>
    )
  }

  const isPending = status === 'submitted' || status === 'streaming'

  return (
    <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6">
      <div className="max-w-3xl mx-auto space-y-6">
        {visibleMessages.map((message) => (
          <Message
            key={message.id}
            message={message}
            onSelectCitation={onSelectCitation}
          />
        ))}

        {pipelineStatus && isPending && (
          <div className="flex gap-3 items-start bg-muted/40 rounded-2xl p-4 border border-border/40 animate-pulse">
            <Loader2 className="h-5 w-5 animate-spin text-primary shrink-0 mt-0.5" />
            <div className="flex-1 min-w-0 space-y-2">
              <p className="text-sm font-medium text-foreground">{pipelineStatus.message}</p>
              <div className="h-1.5 w-full bg-muted rounded-full overflow-hidden">
                <div
                  className="h-full bg-primary transition-all duration-500 rounded-full"
                  style={{ width: `${pipelineStatus.progress * 100}%` }}
                />
              </div>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>
    </div>
  )
}
