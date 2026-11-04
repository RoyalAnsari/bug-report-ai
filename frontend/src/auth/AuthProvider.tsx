import axios from 'axios'
import { useCallback, useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import { clearToken, getToken, setToken } from '../lib/authStorage'
import { AUTH_EXPIRED_EVENT, errorMessage } from '../services/api'
import { getAuthConfig, getMe, loginRequest } from '../services/auth'
import type { AuthUser } from '../types/auth'
import { ANONYMOUS_USER, AuthContext } from './context'
import type { AuthState } from './context'

export default function AuthProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<AuthState['status']>('loading')
  const [authEnabled, setAuthEnabled] = useState(false)
  const [user, setUser] = useState<AuthUser | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    let cancelled = false

    async function start() {
      try {
        const config = await getAuthConfig()
        if (cancelled) return
        if (!config.auth_enabled) {
          setAuthEnabled(false)
          setUser(ANONYMOUS_USER)
          setStatus('ready')
          return
        }
        setAuthEnabled(true)
        if (getToken()) {
          try {
            const me = await getMe()
            if (cancelled) return
            setUser(me)
          } catch (problem) {
            if (axios.isAxiosError(problem) && problem.response?.status === 401) {
              clearToken()
              if (!cancelled) setUser(null)
            } else {
              throw problem
            }
          }
        } else {
          setUser(null)
        }
        if (!cancelled) setStatus('ready')
      } catch (problem) {
        if (cancelled) return
        setError(errorMessage(problem))
        setStatus('error')
      }
    }

    void start()
    return () => {
      cancelled = true
    }
  }, [attempt])

  useEffect(() => {
    function onExpired() {
      setUser(null)
    }
    window.addEventListener(AUTH_EXPIRED_EVENT, onExpired)
    return () => window.removeEventListener(AUTH_EXPIRED_EVENT, onExpired)
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    const response = await loginRequest(email, password)
    setToken(response.access_token)
    setUser({
      id: response.user.id,
      email: response.user.email,
      name: response.user.name,
      role: response.user.role,
    })
  }, [])

  const logout = useCallback(() => {
    clearToken()
    setUser(null)
  }, [])

  const retry = useCallback(() => {
    setError(null)
    setStatus('loading')
    setAttempt((value) => value + 1)
  }, [])

  const value = useMemo<AuthState>(
    () => ({ status, authEnabled, user, error, login, logout, retry }),
    [status, authEnabled, user, error, login, logout, retry],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
