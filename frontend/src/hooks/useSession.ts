import { useEffect, useState } from 'react'

import { supabase } from '@/lib/supabase'

export function useSession() {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    let active = true

    async function loadSession() {
      const { data } = await supabase.auth.getSession()
      if (!active) return
      setIsAuthenticated(Boolean(data.session))
      setIsLoading(false)
    }

    void loadSession()

    const { data: authListener } = supabase.auth.onAuthStateChange((_event, session) => {
      if (!active) return
      setIsAuthenticated(Boolean(session))
      setIsLoading(false)
    })

    return () => {
      active = false
      authListener.subscription.unsubscribe()
    }
  }, [])

  return { isAuthenticated, isLoading }
}
