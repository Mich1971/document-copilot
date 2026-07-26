import { useMemo, useRef, useEffect } from 'react'
import { Message } from './Message'
import { RAGStatus } from './RAGStatus'
import type { UIMessage, ChatStatus } from 'ai'
import type { PipelineStatus, CitationPayload } from '@/lib/citations'
import { LogoMark } from '@/components/Logo'
import { useTranslation } from '@/hooks/useTranslation'

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
  const { t } = useTranslation()
  const bottomRef = useRef<HTMLDivElement>(null)

  const visibleMessages = useMemo(() => {
    return messages.filter((m) => m.role !== 'system')
  }, [messages])

  useEffect(() => {
    // block: 'end' asegura que el fondo del espaciador se alinee con el fondo del contenedor,
    // garantizando que el mensaje quede por encima del input flotante.
    bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [visibleMessages, pipelineStatus])

  if (visibleMessages.length === 0 && status === 'ready') {
    return (
      <div className="flex flex-1 flex-col items-center justify-center text-center p-8">
        <LogoMark className="h-12 w-12 mb-6 text-muted-foreground opacity-20" />
        <p className="text-lg font-medium text-foreground">{t.chat.emptyTitle}</p>
        <p className="text-sm mt-2 max-w-sm text-muted-foreground">
          {t.chat.emptyDesc}
        </p>
      </div>
    )
  }

  const isPending = status === 'submitted' || status === 'streaming'

  return (
    <div className="flex-1 overflow-y-auto p-4 md:p-6 scroll-smooth">
      <div className="max-w-3xl mx-auto flex flex-col gap-2">
        {visibleMessages.map((message) => (
          <Message
            key={message.id}
            message={message}
            onSelectCitation={onSelectCitation}
          />
        ))}

        {pipelineStatus && isPending && (
          <div className="py-4">
            <RAGStatus status={pipelineStatus} />
          </div>
        )}

        {/* Espaciador dinámico: crea un bloque vacío al final de la lista 
            que es más alto que el input flotante, empujando el contenido hacia arriba */}
        <div ref={bottomRef} className="h-36 md:h-48 shrink-0" />
      </div>
    </div>
  )
}