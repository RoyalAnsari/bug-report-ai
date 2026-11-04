import { ANONYMOUS_USER } from './context'
import type { AuthState } from './context'

// Sirf tests ke liye: ek AuthState banata hai jis ke kuch hisse badle ja sakte hain.
export function makeAuthState(overrides: Partial<AuthState> = {}): AuthState {
  return {
    status: 'ready',
    authEnabled: true,
    user: null,
    error: null,
    login: async () => {},
    logout: () => {},
    retry: () => {},
    ...overrides,
  }
}

export const ADMIN = { ...ANONYMOUS_USER, id: 'usr_admin', email: 'admin@example.com', name: 'Admin' }
export const REVIEWER = {
  ...ANONYMOUS_USER,
  id: 'usr_rev',
  email: 'rev@example.com',
  name: 'Reviewer',
  role: 'reviewer' as const,
}
