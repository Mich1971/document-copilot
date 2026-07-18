import { api } from '@/lib/api'
import type { UIMessage } from 'ai'

export interface ThreadSummary {
  id: string
  title: string
  created_at: string
  updated_at: string
  message_count: number
}

export interface ThreadDetail {
  id: string
  title: string
  created_at: string
  updated_at: string
  message_count: number
  messages: UIMessage[]
}

export async function listThreads(): Promise<ThreadSummary[]> {
  return api.get<ThreadSummary[]>('/chats/threads')
}

export async function createThread(title: string): Promise<ThreadSummary> {
  return api.post<ThreadSummary>('/chats/threads', { title })
}

export async function getThreadMessages(threadId: string): Promise<UIMessage[]> {
  const data = await api.get<ThreadDetail>(`/chats/threads/${threadId}`)
  return data.messages ?? []
}

export async function getThreadDetail(threadId: string): Promise<ThreadDetail> {
  return api.get<ThreadDetail>(`/chats/threads/${threadId}`)
}
