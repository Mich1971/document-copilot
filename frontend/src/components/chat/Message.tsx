import { useMemo, useState } from 'react'
import { format } from 'date-fns'
import { User, Copy, Check } from 'lucide-react'
import type { UIMessage } from 'ai'

import { LogoMark } from '@/components/Logo'
import { extractCitations, type CitationPayload } from '@/lib/citations'
import { MarkdownRenderer } from './MarkdownRenderer'
import { cn } from '@/lib/utils'

interface MessageProps {
  message: UIMessage
  onSelectCitation?: (citation: CitationPayload | null) => void
}

export function Message({ message, onSelectCitation }: MessageProps) {
  const [isCopied, setIsCopied] = useState(false)
  const citations = useMemo(() => extractCitations([message]), [message])
  const isUser = message.role === 'user'

  // Casteamos a any para evitar errores estrictos de TS con parts y createdAt
  const msg = message as any
  const parts = msg.parts || []
  const textContent = parts.filter((p: any) => p.type === 'text').map((p: any) => p.text || '').join('')

  const formatTime = (date?: Date | string) => {
    if (!date) return ''
    const d = typeof date === 'string' ? new Date(date) : date
    if (isNaN(d.getTime())) return ''
    return format(d, 'HH:mm')
  }

  const handleCopy = async () => {
    if (!textContent) return
    await navigator.clipboard.writeText(textContent)
    setIsCopied(true)
    setTimeout(() => setIsCopied(false), 2000)
  }

  return (
    <div className={cn("flex w-full gap-4 py-4 group", isUser ? "justify-end" : "justify-start")}>
      {/* Avatar Asistente */}
      {!isUser && (
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md border border-border bg-background shadow-sm mt-1">
          <LogoMark className="h-5 w-5" />
        </div>
      )}

      <div className={cn("flex flex-col gap-1.5 max-w-[85%] md:max-w-[75%]", isUser ? "items-end" : "items-start")}>
        <div className="flex items-center gap-2 text-xs text-muted-foreground px-1">
          <span className="font-medium text-foreground">{isUser ? 'Tú' : 'Document Copilot'}</span>
        </div>

        <div
          className={cn(
            "relative px-4 py-3",
            isUser
              ? "bg-muted text-foreground rounded-2xl rounded-tr-sm"
              : "bg-transparent text-foreground rounded-none px-1 py-1"
          )}
        >
          {isUser ? (
            <div className="whitespace-pre-wrap text-sm">{textContent}</div>
          ) : (
            <MarkdownRenderer
              content={textContent}
              citations={citations}
              onSelectCitation={onSelectCitation}
            />
          )}
        </div>

        {/* Fila de acciones: Hora y Botón de Copiar */}
        <div className={cn(
          "flex items-center gap-2 px-2 text-xs text-muted-foreground transition-opacity duration-200",
          isUser ? "flex-row-reverse" : "flex-row",
          // En móvil siempre visible (opacity-100), en escritorio invisible hasta hacer hover
          "opacity-100 md:opacity-0 md:group-hover:opacity-100"
        )}>
          <span>{formatTime(msg.createdAt)}</span>
          <button
            onClick={handleCopy}
            className="p-1 hover:text-foreground transition-colors rounded-md hover:bg-muted/50"
            title="Copiar mensaje"
            aria-label="Copiar mensaje"
          >
            {isCopied ? <Check className="h-3.5 w-3.5 text-primary" /> : <Copy className="h-3.5 w-3.5" />}
          </button>
        </div>
      </div>

      {/* Avatar Usuario */}
      {isUser && (
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-muted text-muted-foreground mt-1">
          <User className="h-5 w-5" />
        </div>
      )}
    </div>
  )
}