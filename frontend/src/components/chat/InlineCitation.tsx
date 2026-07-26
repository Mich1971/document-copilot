import React from 'react'
import type { CitationPayload } from '@/lib/citations'
import { cn } from '@/lib/utils'

interface InlineCitationProps {
    citation: CitationPayload
    onClick: (citation: CitationPayload) => void
}

export function InlineCitation({ citation, onClick }: InlineCitationProps) {
    return (
        <button
            type="button"
            onClick={() => onClick(citation)}
            className={cn(
                "group relative inline-flex items-center justify-center align-baseline",
                "mx-0.5 px-1.5 py-0.5 rounded-md text-[11px] font-mono font-medium leading-none",
                "bg-muted border border-border/50 text-muted-foreground transition-all",
                "hover:bg-primary hover:text-primary-foreground hover:border-primary",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            )}
            title={citation.documentTitle}
        >
            <span className="sr-only">Ver fuente: </span>
            {citation.citationIndex + 1}
        </button>
    )
}