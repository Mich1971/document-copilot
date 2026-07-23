import { useMemo, useState } from 'react'

import { format } from 'date-fns'
import { Copy, Check, Loader2, FileText, ExternalLink } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import type { UIMessage } from 'ai'

import { extractCitations, type CitationPayload } from '@/lib/citations'

interface MessageProps {
  message: UIMessage
  onSelectCitation?: (citation: CitationPayload | null) => void
}

export function Message({ message, onSelectCitation }: MessageProps) {
  const [isCopied, setIsCopied] = useState(false)
  const citations = useMemo(() => extractCitations([message]), [message])
  const hasCitations = citations.length > 0

  const isAssistant = message.role === 'assistant'
  const isUser = message.role === 'user'
  const msg = message as any

  const formatTime = (date?: Date | string) => {
    if (!date) return ''
    const d = typeof date === 'string' ? new Date(date) : date
    if (isNaN(d.getTime())) return ''
    return format(d, 'HH:mm')
  }

  const handleCopyMessage = async () => {
    const parts = (msg.parts || []) as any[]
    const text = parts.filter((part) => part.type === 'text').map((part) => part.text || '').join('')
    await navigator.clipboard.writeText(text)
    setIsCopied(true)
    setTimeout(() => setIsCopied(false), 2000)
  }

  const renderContent = () => {
    const parts = (msg.parts || []) as any[]
    const text = parts.filter((part) => part.type === 'text').map((part) => part.text || '').join('')

    if (isAssistant && !text && !hasCitations) {
      return (
        <div className="flex items-center gap-2 text-muted-foreground py-1">
          <Loader2 className="h-4 w-4 animate-spin" />
          <span className="text-sm">Pensando…</span>
        </div>
      )
    }

    if (text) {
      return <div className="whitespace-pre-wrap">{text}</div>
    }

    return null
  }

  const renderCitations = () => {
    if (!hasCitations) return null

    return (
      <div className="mt-3 space-y-2">
        <Separator />
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <FileText className="h-3 w-3" />
          <span>Fuentes ({citations.length})</span>
        </div>
        <ScrollArea className="max-h-64">
          <div className="space-y-2 p-1">
            {citations.map((citation, index) => (
              <CitationItem
                key={`${citation.documentId}-${index}`}
                citation={citation}
                index={index}
                onSelect={onSelectCitation}
              />
            ))}
          </div>
        </ScrollArea>
      </div>
    )
  }

  return (
    <div
      className={`flex gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}
      data-message-id={message.id}
    >
      <div
        className={`flex-1 max-w-[85%] flex flex-col ${
          isUser ? 'items-end' : 'items-start'
        }`}
      >
        <div
          className={`inline-block rounded-2xl px-4 py-2 ${
            isUser
              ? 'bg-primary text-primary-foreground rounded-tr-sm'
              : 'bg-muted rounded-tl-sm'
          }`}
        >
          {renderContent()}
        </div>
        {isAssistant && renderCitations()}
        <div className={`flex items-center gap-2 mt-1 text-xs text-muted-foreground ${isUser ? 'flex-row-reverse' : ''}`}>
          <span>{formatTime(msg.createdAt)}</span>
          {(isAssistant || isUser) && (
            <Button
              variant="ghost"
              size="icon"
              className="h-6 w-6"
              onClick={handleCopyMessage}
              aria-label="Copy message"
            >
              {isCopied ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
            </Button>
          )}
        </div>
      </div>
    </div>
  )
}

function CitationItem({ citation, index, onSelect }: { citation: CitationPayload; index: number; onSelect?: (citation: CitationPayload | null) => void }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    await navigator.clipboard.writeText(citation.content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <Card className="bg-muted/30 border-muted-foreground/10">
      <CardContent className="p-3">
        <div className="flex items-start gap-2">
          <span className="text-[10px] font-mono text-muted-foreground shrink-0 mt-0.5">
            [{index + 1}]
          </span>
          <div className="flex-1 min-w-0">
            <p className="font-semibold text-sm truncate" title={citation.documentTitle}>
              {citation.documentTitle}
            </p>
            <p className="text-xs text-muted-foreground mt-1 line-clamp-3 leading-relaxed">
              {citation.content}
            </p>
            <div className="flex items-center justify-between mt-2 pt-2 border-t border-muted-foreground/5">
              <span className="text-[10px] text-muted-foreground/70">
                Chunk: {citation.chunkIndex}
              </span>
              <div className="flex items-center gap-1">
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-6 w-6"
                  onClick={handleCopy}
                  title="Copiar fragmento"
                >
                  {copied ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-6 w-6"
                  title="Ver pasaje fuente"
                  onClick={() => onSelect?.(citation)}
                >
                  <ExternalLink className="h-3 w-3" />
                </Button>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}