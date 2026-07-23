import { useMemo } from 'react'
import { DefaultChatTransport } from 'ai'
import { env } from '@/lib/env'
import { supabase } from '@/lib/supabase'
import type { PipelineStatus } from '@/lib/citations'

class DebugChatTransport extends DefaultChatTransport {
  async sendMessages(options) {
    console.log('[DebugTransport] sendMessages options=', options)
    const result = await super.sendMessages(options)
    console.log('[DebugTransport] sendMessages result type=', result?.constructor?.name ?? result)
    if (result && typeof result === 'object' && typeof result.pipeThrough === 'function') {
      return result.pipeThrough(
        new TransformStream({
          transform(chunk, controller) {
            console.log('[DebugTransport] stream chunk=', chunk)
            controller.enqueue(chunk)
          },
        }),
      )
    }
    return result
  }
}

export function useChatTransport(
  threadId: string,
  setPipelineStatus: (status: PipelineStatus | null) => void,
) {
  return useMemo(() => {
    return new DebugChatTransport({
      api: `${env.apiBaseUrl}/chats/stream`,
      async headers() {
        const { data: { session } } = await supabase.auth.getSession()
        return {
          Authorization: `Bearer ${session?.access_token ?? ''}`,
        }
      },
      prepareSendMessagesRequest({ messages }) {
        return {
          body: {
            messages: messages.map((m) => {
              const parts = m.parts || []
              const textContent = parts
                .filter((p) => p.type === 'text')
                .map((p) => (p as any).text || '')
                .join('')
              return {
                role: m.role,
                content: textContent,
              }
            }),
            thread_id: threadId,
          },
        }
      },
      fetch: async (url, options) => {
        setPipelineStatus({
          stage: 'generation',
          progress: 0.5,
          message: 'Generating response…',
        })
        try {
          const res = await fetch(url, options)
          return res
        } finally {
          setPipelineStatus(null)
        }
      },
    })
  }, [threadId, setPipelineStatus])
}
