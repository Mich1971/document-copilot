import { useEffect } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { MessageSquare, PlusSquare } from 'lucide-react'

import { LogoMark } from '@/components/Logo'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Skeleton } from '@/components/ui/skeleton'
import { useThreads } from '@/hooks/useThreads'
import { useTranslation } from '@/hooks/useTranslation'
import { UserMenu } from './UserMenu'
import { cn } from '@/lib/utils'

interface SidebarProps {
    onNavigate?: () => void
}

export function Sidebar({ onNavigate }: SidebarProps) {
    const location = useLocation()
    const navigate = useNavigate()
    const { t } = useTranslation()
    const { threads, loading, refreshThreads, addThread } = useThreads()

    useEffect(() => {
        void refreshThreads()
    }, [refreshThreads])

    const handleNewChat = async () => {
        try {
            const newThread = await addThread(t.chat.newChat)
            navigate(`/chats/${newThread.id}`)
            onNavigate?.()
        } catch (error) {
            console.error('Error creating thread:', error)
        }
    }

    return (
        <div className="flex h-full flex-col bg-muted/10">
            {/* Header / Logo */}
            <div className="flex h-14 items-center px-4 border-b border-border/50">
                <Link to="/chats" onClick={onNavigate} className="flex items-center gap-2 font-semibold hover:opacity-80 transition-opacity">
                    <LogoMark className="h-6 w-6" />
                    <span className="tracking-tight">Document Copilot</span>
                </Link>
            </div>

            {/* New Chat Button */}
            <div className="p-4 pb-2">
                <Button onClick={handleNewChat} className="w-full justify-start gap-2 shadow-sm" variant="default">
                    <PlusSquare className="h-4 w-4" />
                    {t.chat.newChat}
                </Button>
            </div>

            {/* Thread List */}
            <ScrollArea className="flex-1 px-2">
                <div className="space-y-1 py-2">
                    {loading ? (
                        Array.from({ length: 5 }).map((_, i) => (
                            <div key={i} className="flex items-center gap-2 px-2 py-2">
                                <Skeleton className="h-4 w-4 rounded" />
                                <Skeleton className="h-4 flex-1 rounded" />
                            </div>
                        ))
                    ) : threads.length === 0 ? (
                        <p className="px-4 py-6 text-center text-xs text-muted-foreground">
                            No hay conversaciones recientes.
                        </p>
                    ) : (
                        threads.map((thread) => {
                            const isActive = location.pathname === `/chats/${thread.id}`
                            return (
                                <Link
                                    key={thread.id}
                                    to={`/chats/${thread.id}`}
                                    onClick={onNavigate}
                                    className={cn(
                                        "flex items-center gap-2 rounded-md px-2 py-2 text-sm transition-colors",
                                        isActive
                                            ? "bg-muted font-medium text-foreground"
                                            : "text-muted-foreground hover:bg-muted/50 hover:text-foreground"
                                    )}
                                >
                                    <MessageSquare className="h-4 w-4 shrink-0" />
                                    <span className="truncate">{thread.title}</span>
                                </Link>
                            )
                        })
                    )}
                </div>
            </ScrollArea>

            {/* Footer / User Menu */}
            <div className="p-2 border-t border-border/50">
                <UserMenu />
            </div>
        </div>
    )
}