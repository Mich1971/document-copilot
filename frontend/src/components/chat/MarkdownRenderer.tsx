import React from 'react'
import { InlineCitation } from './InlineCitation'
import type { CitationPayload } from '@/lib/citations'

interface MarkdownRendererProps {
    content: string
    citations: CitationPayload[]
    onSelectCitation?: (citation: CitationPayload | null) => void
}

export function MarkdownRenderer({ content, citations, onSelectCitation }: MarkdownRendererProps) {
    const paragraphs = content.split('\n').filter((p) => p.trim() !== '')

    return (
        <div className="space-y-4 text-sm leading-relaxed">
            {paragraphs.map((paragraph, pIdx) => {
                const parts = paragraph.split(/\[(\d+)\]/g)

                return (
                    <p key={pIdx} className="m-0">
                        {parts.map((part, i) => {
                            if (i % 2 === 1) {
                                const citationIndex = parseInt(part, 10) - 1
                                const citation = citations.find((c) => c.citationIndex === citationIndex)

                                if (citation && onSelectCitation) {
                                    return (
                                        <InlineCitation
                                            key={i}
                                            citation={citation}
                                            onClick={onSelectCitation}
                                        />
                                    )
                                }
                                return <span key={i}>[{part}]</span>
                            }

                            return <React.Fragment key={i}>{part}</React.Fragment>
                        })}
                    </p>
                )
            })}
        </div>
    )
}