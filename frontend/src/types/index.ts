import type { UIMessage } from 'ai'

// ==========================================
// AUTH & USER TYPES
// ==========================================
export interface UserProfile {
    id: string
    email: string
}

export interface MeResponse {
    ok: boolean
    user: UserProfile
}

// ==========================================
// CHAT & THREAD TYPES
// ==========================================
export interface ThreadSummary {
    id: string
    title: string
    created_at: string
    updated_at: string
    message_count: number
}

export interface ThreadDetail extends ThreadSummary {
    messages: UIMessage[]
}

// ==========================================
// RAG, CITATIONS & PIPELINE TYPES
// ==========================================
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

// ==========================================
// I18N (INTERNATIONALIZATION) TYPES
// ==========================================
export type Language = 'es' | 'en' | 'pt'

// ==========================================
// API & HTTP TYPES
// ==========================================
export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'

export interface RequestOptions {
    method?: HttpMethod
    body?: unknown
    headers?: Record<string, string>
    accessToken?: string | null
    timeoutMs?: number
}