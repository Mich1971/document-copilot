import { Navigate, Outlet } from 'react-router-dom'

import { useSession } from '@/hooks/useSession'

export function ProtectedRoute() {
  const { isAuthenticated, isLoading } = useSession()

  if (isLoading) {
    return null
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return <Outlet />
}
