import { useCallback, useState } from 'react'
import { listThreads, createThread, type ThreadSummary } from '@/lib/chat'

export function useThreads() {
  const [threads, setThreads] = useState<ThreadSummary[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  const refreshThreads = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await listThreads()
      setThreads(data)
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to load threads'))
    } finally {
      setLoading(false)
    }
  }, [])

  const addThread = useCallback(async (title: string) => {
    setError(null)
    try {
      const newThread = await createThread(title)
      setThreads((prev) => [newThread, ...prev])
      return newThread
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to create thread'))
      throw err
    }
  }, [])

  const removeThread = useCallback((threadId: string) => {
    setThreads((prev) => prev.filter((t) => t.id !== threadId))
  }, [])

  const updateThread = useCallback((threadId: string, updates: Partial<ThreadSummary>) => {
    setThreads((prev) =>
      prev.map((t) => (t.id === threadId ? { ...t, ...updates } : t)),
    )
  }, [])

  return {
    threads,
    loading,
    error,
    refreshThreads,
    addThread,
    removeThread,
    updateThread,
  }
}