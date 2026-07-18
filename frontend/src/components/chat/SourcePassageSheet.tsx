import { useState, useEffect } from 'react'
import { X, Copy, Check, FileText, ChevronRight } from 'lucide-react'
import type { CitationPayload } from '@/lib/citations'
import { Button } from '@/components/ui/button'

interface SourcePassageSheetProps {
  citation: CitationPayload | null
  onOpenChange: (open: boolean) => void
}

export function SourcePassageSheet({ citation, onOpenChange }: SourcePassageSheetProps) {
  const [copied, setCopied] = useState(false)
  const isOpen = !!citation

  const handleCopy = async () => {
    if (!citation) return
    await navigator.clipboard.writeText(citation.content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  // Handle escape key to close sheet
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onOpenChange(false)
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, onOpenChange])

  return (
    <>
      {/* Backdrop */}
      <div
        className={`fixed inset-0 z-40 bg-background/40 backdrop-blur-sm transition-opacity duration-300 ${
          isOpen ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'
        }`}
        onClick={() => onOpenChange(false)}
      />

      {/* Drawer */}
      <div
        className={`fixed inset-y-0 right-0 z-50 flex w-full max-w-md flex-col border-l border-border bg-background shadow-2xl transition-transform duration-300 ease-in-out sm:max-w-lg ${
          isOpen ? 'translate-x-0' : 'translate-x-full'
        }`}
        role="dialog"
        aria-modal="true"
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-border p-4">
          <div className="flex items-center gap-2 text-primary">
            <FileText className="h-5 w-5" />
            <h2 className="text-base font-semibold text-foreground">Source Document Passage</h2>
          </div>
          <Button
            variant="ghost"
            size="icon"
            className="rounded-full h-8 w-8 hover:bg-muted"
            onClick={() => onOpenChange(false)}
            aria-label="Close panel"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>

        {/* Content */}
        {citation && (
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {/* Title / Document details */}
            <div className="space-y-1.5">
              <span className="text-[10px] font-mono font-semibold uppercase tracking-wider text-primary bg-primary/10 px-2 py-0.5 rounded">
                Citation [{citation.citationIndex + 1}]
              </span>
              <h3 className="text-lg font-semibold text-foreground leading-snug">
                {citation.documentTitle}
              </h3>
              <div className="flex items-center gap-1.5 text-xs text-muted-foreground mt-2">
                <span>Chunk Index: {citation.chunkIndex}</span>
                <ChevronRight className="h-3 w-3" />
                <span>Search Score: {citation.score.toFixed(4)}</span>
              </div>
            </div>

            {/* Excerpt Content Card */}
            <div className="relative rounded-2xl border border-border/80 bg-muted/30 p-5">
              <div className="absolute top-4 right-4">
                <Button
                  variant="outline"
                  size="icon"
                  className="h-8 w-8 rounded-lg bg-background hover:bg-muted"
                  onClick={handleCopy}
                  title="Copy text passage"
                >
                  {copied ? (
                    <Check className="h-3.5 w-3.5 text-success" />
                  ) : (
                    <Copy className="h-3.5 w-3.5" />
                  )}
                </Button>
              </div>
              <p className="text-sm text-foreground leading-relaxed whitespace-pre-wrap pr-10">
                {citation.content}
              </p>
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="border-t border-border p-4 bg-muted/20">
          <Button className="w-full" onClick={() => onOpenChange(false)}>
            Close Panel
          </Button>
        </div>
      </div>
    </>
  )
}
