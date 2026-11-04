import type { Role } from './auth'

export interface ManagedUser {
  id: string
  email: string
  name: string
  role: Role
  is_active: boolean
  created_at: string | null
  last_login_at: string | null
}

export interface NewUser {
  email: string
  name: string
  role: Role
  password: string
}

export interface UserChanges {
  name?: string
  role?: Role
  is_active?: boolean
}
