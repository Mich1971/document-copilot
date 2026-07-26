import { useRef, useCallback, useState, type FormEvent } from 'react'
import { Send, Square } from 'lucide-react'
import type { ChatStatus } from 'ai'
import { Textarea } from '@/components/ui/textarea'
import { Button } from '@/components/ui/button'
import { useTranslation } from '@/hooks/useTranslation'

interface ChatInputProps {
  status: ChatStatus
  onSend: (text: string) => void
  onStop: () => void
}

export function ChatInput({ status, onSend, onStop }: ChatInputProps) {
  const { t } = useTranslation()
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const [input, setInput] = useState('')

  const isPending = status === 'submitted' || status === 'streaming'

  const handleSubmit = useCallback(
    (e: FormEvent<HTMLFormElement>) => {
      e.preventDefault()
      if (!input.trim() || isPending) return
      onSend(input.trim())
      setInput('')
      setTimeout(() => textareaRef.current?.focus(), 10)
    },
    [input, isPending, onSend],
  )

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault()
        const form = e.currentTarget.form
        if (form) form.requestSubmit()
      }
    },
    [],
  )

  return (
    <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-background via-background to-transparent pt-10 pb-6 px-4">
      <form
        onSubmit={handleSubmit}
        className="mx-auto max-w-3xl relative flex items-end gap-2 rounded-2xl border border-border bg-background p-2 shadow-lg shadow-black/5 dark:shadow-black/20 focus-within:ring-1 focus-within:ring-ring transition-shadow"
      >
        <Textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={isPending ? t.chat.generating : t.chat.placeholder}
          disabled={isPending}
          className="min-h-[44px] max-h-[200px] resize-none w-full border-0 bg-transparent px-3 py-3 text-sm shadow-none focus-visible:ring-0"
          rows={1}
        />

        {isPending ? (
          <Button
            type="button"
            onClick={onStop}
            size="icon"
            className="mb-1 mr-1 h-8 w-8 shrink-0 rounded-xl bg-muted text-muted-foreground hover:bg-muted hover:text-foreground"
          >
            <Square className="h-3.5 w-3.5 fill-current" />
          </Button>
        ) : (
          <Button
            type="submit"
            disabled={!input.trim()}
            size="icon"
            className="mb-1 mr-1 h-8 w-8 shrink-0 rounded-xl transition-transform active:scale-95"
          >
            <Send className="h-3.5 w-3.5" />
          </Button>
        )}
      </form>
      <div className="mx-auto max-w-3xl mt-2 text-center">
        <p className="text-[10px] text-muted-foreground">
          Document Copilot puede cometer errores. Verifica la información en los documentos fuente.
        </p>
      </div>
    </div>
  )
}