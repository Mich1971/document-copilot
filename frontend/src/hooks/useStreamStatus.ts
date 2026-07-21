import { useEffect, useRef, useCallback } from 'react'
import { env } from '@/lib/env'
import { supabase } from '@/lib/supabase'
import type { PipelineStatus } from '@/lib/citations'

export function useStreamStatus(threadId: string) {
  const abortRef = useRef<AbortController | null>(null)

  const connect = useCallback(async () => {
    abortRef.current?.abort()
    const controller = new AbortController()
    abortRef.current = controller

    const { data: { session } } = await supabase.auth.getSession()
    const token = session?.access_token ?? ''

    const res = await fetch(`${env.apiBaseUrl}/chats/threads/${threadId}/stream-status`, {
      headers: {
        Authorization: `Bearer ${token}`,
        Accept: 'text/event-stream',
      },
      signal: controller.signal,
    })

    if (!res.ok) {
      return { pipelineStatus: null as PipelineStatus | null, error: new Error(`Stream status failed: ${res.status}`) }
    }

    const reader = res.body?.getReader()
    if (!reader) {
      return { pipelineStatus: null as PipelineStatus | null, error: new Error('No stream body') }
    }

    const decoder = new TextDecoder()
    let buffer = ''
    let currentStatus: PipelineStatus | null = null

    try {
      while (true) {
        const { value, done } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() ?? ''

        for (const line of lines) {
          const trimmed = line.trim()
          if (!trimmed || !trimmed.startsWith('data:')) continue

          const payload = trimmed.slice(5).trim()
          try {
            const data = JSON.parse(payload)
            if (data?.type === 'status' && data.stage) {
              currentStatus = {
                stage: data.stage,
                progress: typeof data.progress === 'number' ? data.progress : 0,
                message: typeof data.message === 'string' ? data.message : '',
              }
            }
          } catch {
            // ignore malformed JSON
          }
        }
      }
    } catch (err) {
      if ((err as Error).name !== 'AbortError') {
        return { pipelineStatus: currentStatus, error: err instanceof Error ? err : new Error('Stream error') }
      }
    }

    return { pipelineStatus: null, error: null }
  }, [threadId])

  useEffect(() => {
    return () => {
      abortRef.current?.abort()
    }
  }, [])

  return { connect, abort: () => abortRef.current?.abort() }
}
