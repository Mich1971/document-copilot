import { Loader2, Search, FileText, CheckCircle2 } from 'lucide-react'
import type { PipelineStatus } from '@/lib/citations'

interface RAGStatusProps {
    status: PipelineStatus
}

export function RAGStatus({ status }: RAGStatusProps) {
    const getIcon = () => {
        switch (status.stage) {
            case 'retrieval': return <Search className="h-4 w-4 text-muted-foreground animate-pulse" />
            case 'grounding': return <FileText className="h-4 w-4 text-muted-foreground animate-pulse" />
            case 'complete': return <CheckCircle2 className="h-4 w-4 text-primary" />
            default: return <Loader2 className="h-4 w-4 text-muted-foreground animate-spin" />
        }
    }

    return (
        <div className="flex items-center gap-3 py-2 px-1">
            <div className="flex h-8 w-8 items-center justify-center rounded-full border border-border bg-muted/30">
                {getIcon()}
            </div>
            <div className="flex flex-col">
                <span className="text-xs font-medium text-foreground">
                    {status.message}
                </span>
                <div className="mt-1 h-1 w-32 overflow-hidden rounded-full bg-muted">
                    <div
                        className="h-full bg-primary transition-all duration-500 ease-out"
                        style={{ width: `${status.progress * 100}%` }}
                    />
                </div>
            </div>
        </div>
    )
}