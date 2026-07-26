import React, { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { AuthLayout } from '@/components/AuthLayout'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { BetaCredentials } from '@/components/auth/BetaCredentials'
import { supabase } from '@/lib/supabase'
import { env } from '@/lib/env'
import { useTranslation } from '@/hooks/useTranslation'

export function Login() {
  const navigate = useNavigate()
  const { t } = useTranslation()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setIsSubmitting(true)

    const { error: signInError } = await supabase.auth.signInWithPassword({
      email: email.trim(),
      password,
    })

    setIsSubmitting(false)

    if (signInError) {
      setError(signInError.message)
      return
    }

    navigate('/chats', { replace: true })
  }

  return (
    <AuthLayout
      title={t.auth.signIn}
      description={t.auth.signInDesc}
    >
      <form className="space-y-4" onSubmit={handleSubmit}>
        <div className="space-y-2">
          <Label htmlFor="email">{t.auth.email}</Label>
          <Input
            id="email"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="usted@fiduciapay.com"
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="password">{t.auth.password}</Label>
          <Input
            id="password"
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
        </div>

        {error ? (
          <p className="text-sm font-medium text-destructive" role="alert">
            {error}
          </p>
        ) : null}

        <Button type="submit" className="w-full" disabled={isSubmitting}>
          {isSubmitting ? t.auth.signingIn : t.auth.signIn}
        </Button>
      </form>

      {env.showBetaCredentials && <BetaCredentials />}

      <p className="mt-6 text-center text-sm text-muted-foreground">
        {t.auth.noAccount}{' '}
        <Link to="/signup" className="text-foreground font-medium underline-offset-4 hover:underline">
          {t.auth.signUp}
        </Link>
      </p>
    </AuthLayout>
  )
}