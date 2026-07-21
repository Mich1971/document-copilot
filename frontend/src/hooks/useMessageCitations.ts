import { useCallback } from 'react'
import type { CitationPayload } from '@/lib/citations'
import { api } from '@/lib/api'

const citationCache = new Map<string, CitationPayload[]>()

export function useMessageCitations() {
  const fetchCitations = useCallback(async (messageId: string): Promise<CitationPayload[]> => {
    if (citationCache.has(messageId)) {
      return citationCache.get(messageId) ?? []
    }

    const data = await api.get<Array<{
      chunk_id: string
      chunk_index: number | null
      excerpt: string
      ticker: string
      company_name: string | null
      form: string
      filing_date: string
      page: string | null
      section: string | null
    }>>(`/chats/messages/${messageId}/citations`)

    const citations: CitationPayload[] = data.map((row, index) => ({
      citationIndex: index,
      documentId: row.chunk_id,
      documentTitle: `${row.company_name ?? row.ticker} — ${row.form} (${row.filing_date})`,
      chunkIndex: row.chunk_index ?? 0,
      content: row.excerpt,
      score: 0,
    }))

    citationCache.set(messageId, citations)
    return citations
  }, [])

  return { fetchCitations }
}
