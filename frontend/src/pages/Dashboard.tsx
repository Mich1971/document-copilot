import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { AuthStateBadge } from '@/components/AuthStateBadge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { api } from '@/lib/api'
import { supabase } from '@/lib/supabase'

type MeResponse = {
  ok: boolean
  user: {
    id: string
    email: string
  }
}

export function Dashboard() {
  const navigate = useNavigate()
  const [userEmail, setUserEmail] = useState<string | null>(null)
  const [message, setMessage] = useState<string>('Loading your session…')
  const [error, setError] = useState<string | null>(null)
  const [backendResponse, setBackendResponse] = useState<MeResponse | null>(null)
  const [authState, setAuthState] = useState<'loading' | 'authenticated' | 'error'>('loading')

  useEffect(() => {
    let active = true

    async function loadSession() {
      const { data } = await supabase.auth.getSession()
      const currentUser = data.session?.user

      if (!currentUser) {
        navigate('/login', { replace: true })
        return
      }

      try {
        const result = await api.get<MeResponse>('/auth/me')
        if (!active) return
        setBackendResponse(result)
        setUserEmail(result.user.email)
        setMessage(`Authenticated as ${result.user.email}`)
        setAuthState('authenticated')
      } catch (err) {
        if (!active) return
        const messageText = err instanceof Error ? err.message : 'Incapaz de verificar su sesión.'
        setError(messageText)
        setAuthState('error')
      }
    }

    void loadSession()

    return () => {
      active = false
    }
  }, [navigate])

  async function handleSignOut() {
    await supabase.auth.signOut()
    navigate('/login', { replace: true })
  }

  return (
    <div className="min-h-screen bg-background px-4 py-10">
      <div className="mx-auto flex max-w-3xl flex-col gap-4">
        <div className="flex items-center justify-between gap-4">
          <div>
            <p className="text-sm font-medium uppercase tracking-[0.3em] text-muted-foreground">
              Area Protegida
            </p>
            <h1 className="text-3xl font-semibold tracking-tight">Dashboard</h1>
          </div>
          <div className="flex items-center gap-2">
            <AuthStateBadge
              label={authState === 'authenticated' ? 'Authenticated' : authState === 'error' ? 'Auth error' : 'Checking session'}
              tone={authState === 'authenticated' ? 'success' : authState === 'error' ? 'error' : 'default'}
            />
            <Button variant="outline" onClick={handleSignOut}>
              Sign out
            </Button>
          </div>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Verificacion de sesión</CardTitle>
            <CardDescription>
              Esta pantalla prueba que el token de Supabase esta siendo enviado al backend.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 text-sm">
            <p>{message}</p>
            {userEmail ? <p className="font-medium">Signed in as {userEmail}</p> : null}
            {error ? <p className="text-destructive">{error}</p> : null}
            {backendResponse ? (
              <div className="rounded-lg border border-border/70 bg-muted/40 p-3">
                <p className="mb-2 text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground">
                  Backend response
                </p>
                <pre className="overflow-x-auto whitespace-pre-wrap wrap-break-word text-xs text-foreground">
                  {JSON.stringify(backendResponse, null, 2)}
                </pre>
              </div>
            ) : null}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
