import { createContext } from 'react'
import type { AuthUser } from '../types/auth'

export interface AuthState {
  status: 'loading' | 'ready' | 'error'
  authEnabled: boolean
  user: AuthUser | null
  error: string | null
  login: (email: string, password: string) => Promise<void>
  logout: () => void
  retry: () => void
}

// Server par login band ho (AUTH_ENABLED=false) to har koi admin maana jata hai.
export const ANONYMOUS_USER: AuthUser = {
  id: 'anonymous',
  email: '',
  name: 'Authentication disabled',
  role: 'admin',
}

// Default wahi hai jo "login band" ka hota hai, taake provider ke baghair bhi components chalein.
export const AuthContext = createContext<AuthState>({
  status: 'ready',
  authEnabled: false,
  user: ANONYMOUS_USER,
  error: null,
  login: async () => {},
  logout: () => {},
  retry: () => {},
})
