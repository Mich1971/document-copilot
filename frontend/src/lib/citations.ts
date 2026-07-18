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

interface SourceDocumentPart {
  type: 'source'
  sourceType: 'document'
  documentId: string
  documentTitle: string
  chunkIndex: number
  content: string
  score: number
}

function isSourceDocumentPart(part: unknown): part is SourceDocumentPart {
  return (
    typeof part === 'object' &&
    part !== null &&
    'type' in part &&
    part.type === 'source' &&
    'sourceType' in part &&
    part.sourceType === 'document'
  )
}

export function extractCitations(messages: UIMessage[]): CitationPayload[] {
  const citations: CitationPayload[] = []
  
  for (const message of messages) {
    if (message.role === 'assistant' && message.parts) {
      for (const part of message.parts) {
        if (isSourceDocumentPart(part)) {
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
