import React from 'react'
import { Info } from 'lucide-react'

export function BetaCredentials() {
    return (
        <div className="mt-6 rounded-lg border border-border bg-muted/30 p-4 text-sm text-muted-foreground">
            <div className="flex items-center gap-2 font-medium text-foreground mb-2">
                <Info className="h-4 w-4" />
                <span>Credenciales de Beta Testing</span>
            </div>
            <div className="space-y-1 font-mono text-xs">
                <p>Email: <span className="bg-background border border-border px-1.5 py-0.5 rounded select-all">tester@fiduciapay.com</span></p>
                <p>Pass: <span className="bg-background border border-border px-1.5 py-0.5 rounded select-all">password123</span></p>
            </div>
        </div>
    )
}