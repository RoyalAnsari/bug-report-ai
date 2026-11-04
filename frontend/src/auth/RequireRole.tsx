import type { ReactNode } from 'react'
import type { Role } from '../types/auth'
import { useAuth } from './useAuth'

export default function RequireRole({ roles, children }: { roles: Role[]; children: ReactNode }) {
  const auth = useAuth()

  if (auth.user && !roles.includes(auth.user.role)) {
    return (
      <div role="alert" className="rounded-md border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
        You do not have permission to open this page. Ask an admin if you need access.
      </div>
    )
  }

  return <>{children}</>
}
