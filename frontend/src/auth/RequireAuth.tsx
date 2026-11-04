import type { ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from './useAuth'

export default function RequireAuth({ children }: { children: ReactNode }) {
  const auth = useAuth()
  const location = useLocation()

  if (auth.status === 'loading') {
    return (
      <p role="status" className="p-6 text-sm text-slate-600">
        Loading...
      </p>
    )
  }

  if (auth.status === 'error') {
    return (
      <div role="alert" className="mx-auto max-w-md p-6 text-sm text-slate-800">
        <p className="mb-3">{auth.error ?? 'Cannot reach the server.'}</p>
        <button
          type="button"
          onClick={auth.retry}
          className="rounded-md bg-indigo-600 px-3 py-1.5 font-medium text-white hover:bg-indigo-700"
        >
          Try again
        </button>
      </div>
    )
  }

  if (auth.authEnabled && auth.user === null) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  }

  return <>{children}</>
}
