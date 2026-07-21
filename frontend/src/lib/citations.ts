import type { UIMessage } from 'ai'

export interface CitationPayload {
  citationIndex: number
  documentId: string
  documentTitle: string
  chunkIndex: number
  content: string
  score: number
}

export interface PipelineStatus {
  stage: 'retrieval' | 'generation' | 'grounding' | 'complete'
  progress: number
  message: string
}

export type PipelineStatusState = PipelineStatus | null

interface CitationPart {
  type: 'citation'
  id: string
  citation: {
    chunkId: string
    chunkIndex: number | null
    excerpt: string
    ticker: string
    companyName: string | null
    form: string
    filingDate: string
    page: string | null
    section: string | null
  }
}

interface SourceDocumentPart {
  type: 'source'
  sourceType: 'document'
  documentId: string
  documentTitle: string
  chunkIndex: number
  content: string
  score: number
}

function isCitationPart(part: unknown): part is CitationPart {
  return (
    typeof part === 'object' &&
    part !== null &&
    (part as CitationPart).type === 'citation' &&
    'citation' in (part as Record<string, unknown>)
  )
}

function isSourceDocumentPart(part: unknown): part is SourceDocumentPart {
  return (
    typeof part === 'object' &&
    part !== null &&
    (part as Record<string, unknown>).type === 'source' &&
    (part as Record<string, unknown>).sourceType === 'document'
  )
}

export function extractCitations(messages: UIMessage[]): CitationPayload[] {
  const citations: CitationPayload[] = []

  for (const message of messages) {
    if (message.role === 'assistant' && message.parts) {
      for (const part of message.parts) {
        if (isCitationPart(part)) {
          const c = (part as CitationPart).citation
          citations.push({
            citationIndex: citations.length,
            documentId: c.chunkId,
            documentTitle: `${c.companyName ?? c.ticker} — ${c.form} (${c.filingDate})`,
            chunkIndex: c.chunkIndex ?? 0,
            content: c.excerpt,
            score: 0,
          })
        } else if (isSourceDocumentPart(part)) {
          const sourcePart = part as SourceDocumentPart
          citations.push({
            citationIndex: citations.length,
            documentId: sourcePart.documentId,
            documentTitle: sourcePart.documentTitle,
            chunkIndex: sourcePart.chunkIndex,
            content: sourcePart.content,
            score: sourcePart.score,
          })
        }
      }
    }
  }

  return citations
}

export function getCitationByIndex(citations: CitationPayload[], index: number): CitationPayload | null {
  return citations[index] ?? null
}