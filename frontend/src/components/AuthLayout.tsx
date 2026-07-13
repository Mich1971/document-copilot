import type { ReactNode } from 'react'

import { Card, CardContent } from '@/components/ui/card'

type AuthLayoutProps = {
  title: string
  description: string
  children: ReactNode
}

export function AuthLayout({ title, description, children }: AuthLayoutProps) {
  return (
    <div className="min-h-screen bg-background px-4 py-12">
      <div className="mx-auto flex max-w-md flex-col gap-6">
        <div className="space-y-2 text-center">
          <p className="text-sm font-medium uppercase tracking-[0.3em] text-muted-foreground">
            Document Copilot
          </p>
          <h1 className="text-3xl font-semibold tracking-tight">{title}</h1>
          <p className="text-sm text-muted-foreground">{description}</p>
        </div>

        <Card className="border-border/70 shadow-sm">
          <CardContent className="p-6">{children}</CardContent>
        </Card>
      </div>
    </div>
  )
}
