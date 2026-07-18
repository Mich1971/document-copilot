import { useRef, useCallback, useState, type FormEvent } from 'react'
import { Send, Square } from 'lucide-react'
import type { ChatStatus } from 'ai'
import { Textarea } from '@/components/ui/textarea'
import { Button } from '@/components/ui/button'

interface ChatInputProps {
  status: ChatStatus
  onSend: (text: string) => void
  onStop: () => void
}

export function ChatInput({ status, onSend, onStop }: ChatInputProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const [input, setInput] = useState('')

  const isPending = status === 'submitted' || status === 'streaming'

  const handleSubmit = useCallback(
    (e: FormEvent<HTMLFormElement>) => {
      e.preventDefault()
      if (!input.trim() || isPending) return
      onSend(input.trim())
      setInput('')
      // Keep focus on textarea for subsequent inputs
      setTimeout(() => textareaRef.current?.focus(), 10)
    },
    [input, isPending, onSend],
  )

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault()
        // Find and submit the form
        const form = e.currentTarget.form
        if (form) {
          form.requestSubmit()
        }
      }
    },
    [],
  )

  return (
    <div className="w-full border-t border-border bg-background/80 backdrop-blur-md p-4">
      <form onSubmit={handleSubmit} className="max-w-3xl mx-auto flex gap-3 items-end">
        <div className="relative flex-1 bg-muted/50 hover:bg-muted/80 focus-within:bg-muted focus-within:ring-2 focus-within:ring-primary/20 rounded-2xl border border-border/60 transition-all duration-200">
          <Textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={isPending ? 'Generating response…' : 'Ask a question about the filings…'}
            disabled={isPending}
            className="min-h-[48px] max-h-[200px] resize-none w-full bg-transparent border-0 ring-0 focus-visible:ring-0 focus-visible:ring-offset-0 px-4 py-3 text-sm"
            rows={1}
          />
        </div>

        {isPending ? (
          <Button
            type="button"
            onClick={onStop}
            size="icon"
            className="h-[48px] w-[48px] rounded-2xl shrink-0 bg-destructive text-destructive-foreground hover:bg-destructive/90 transition-all duration-200"
            aria-label="Stop generating"
          >
            <Square className="h-4 w-4 fill-current animate-pulse" />
          </Button>
        ) : (
          <Button
            type="submit"
            disabled={!input.trim()}
            size="icon"
            className="h-[48px] w-[48px] rounded-2xl shrink-0 bg-primary hover:bg-primary/95 hover:scale-[1.02] active:scale-[0.98] disabled:scale-100 disabled:opacity-50 disabled:pointer-events-none transition-all duration-200"
            aria-label="Send message"
          >
            <Send className="h-4 w-4" />
          </Button>
        )}
      </form>
    </div>
  )
}
