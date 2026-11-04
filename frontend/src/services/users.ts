import type { ManagedUser, NewUser, UserChanges } from '../types/users'
import { api } from './api'

export async function listUsers(): Promise<ManagedUser[]> {
  const { data } = await api.get<ManagedUser[]>('/users')
  return data
}

export async function createUser(user: NewUser): Promise<ManagedUser> {
  const { data } = await api.post<ManagedUser>('/users', user)
  return data
}

export async function updateUser(id: string, changes: UserChanges): Promise<ManagedUser> {
  const { data } = await api.patch<ManagedUser>(`/users/${encodeURIComponent(id)}`, changes)
  return data
}

export async function resetUserPassword(id: string, newPassword: string): Promise<void> {
  await api.put(`/users/${encodeURIComponent(id)}/password`, { new_password: newPassword })
}
