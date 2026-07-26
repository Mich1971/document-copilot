import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import { Menu } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Sheet, SheetContent, SheetTrigger, SheetTitle } from '@/components/ui/sheet'
import { Sidebar } from './Sidebar'

export function AppLayout() {
    const [mobileOpen, setMobileOpen] = useState(false)

    return (
        <div className="flex h-screen w-full bg-background overflow-hidden">
            {/* Desktop Sidebar */}
            <aside className="hidden md:flex w-[260px] flex-col border-r border-border">
                <Sidebar />
            </aside>

            {/* Main Content Area */}
            <div className="flex flex-1 flex-col min-w-0 overflow-hidden">
                {/* Mobile Header */}
                <header className="md:hidden flex h-14 items-center border-b border-border px-4 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 z-10">
                    <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
                        <SheetTrigger asChild>
                            <Button variant="ghost" size="icon" className="-ml-2 mr-2">
                                <Menu className="h-5 w-5" />
                                <span className="sr-only">Toggle menu</span>
                            </Button>
                        </SheetTrigger>
                        <SheetContent side="left" className="p-0 w-[280px] border-r-border">
                            <SheetTitle className="sr-only">Menú de navegación</SheetTitle>
                            <Sidebar onNavigate={() => setMobileOpen(false)} />
                        </SheetContent>
                    </Sheet>
                    <span className="font-semibold tracking-tight">Document Copilot</span>
                </header>

                {/* Page Content */}
                <main className="flex-1 flex flex-col min-w-0 overflow-hidden relative">
                    <Outlet />
                </main>
            </div>
        </div>
    )
}