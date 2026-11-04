export type Role = 'admin' | 'reviewer'

export interface AuthUser {
  id: string
  email: string
  name: string
  role: Role
}

export interface AuthConfig {
  auth_enabled: boolean
}

export interface LoginResponse {
  access_token: string
  token_type: string
  expires_in: number
  user: AuthUser & { is_active: boolean }
}
