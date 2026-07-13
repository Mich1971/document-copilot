import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { LogoMark } from '@/components/Logo'
import { PromptSuggestion } from '@/components/ui/prompt-suggestion'
import { useThreads } from '@/hooks/useThreads'
import { EXAMPLE_QUESTIONS } from '@/lib/suggestions'

export function ChatEmptyPage() {
  const navigate = useNavigate()
  const { createNewThread } = useThreads()
  const [isStarting, setIsStarting] = useState(false)

  async function startConversation(prompt?: string) {
    if (isStarting) return
    setIsStarting(true)
    try {
      const id = await createNewThread()
      navigate(`/chats/${id}`, prompt ? { state: { initialPrompt: prompt } } : undefined)
    } finally {
      setIsStarting(false)
    }
  }

  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-8 p-6">
      <div className="flex flex-col items-center gap-4 text-center">
        <LogoMark className="size-12" />
        <div className="space-y-1.5">
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">
            How can I help with your filings?
          </h1>
          <p className="max-w-md text-sm text-muted-foreground">
            Ask a question about SEC filings. Every answer is grounded in source documents
            with verifiable citations.
          </p>
        </div>
      </div>

      <div className="grid w-full max-w-xl gap-2 sm:grid-cols-2">
        {EXAMPLE_QUESTIONS.map((question) => (
          <PromptSuggestion
            key={question}
            variant="outline"
            size="default"
            className="h-auto justify-start rounded-xl px-4 py-3 text-left text-sm font-normal whitespace-normal"
            disabled={isStarting}
            onClick={() => void startConversation(question)}
          >
            {question}
          </PromptSuggestion>
        ))}
      </div>
    </div>
  )
}
