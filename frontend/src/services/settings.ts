import type { SettingsResponse, SettingsValues } from '../types/settings'
import { api } from './api'

export async function getSettings(): Promise<SettingsResponse> {
  const { data } = await api.get<SettingsResponse>('/settings')
  return data
}

export async function saveSettings(values: SettingsValues): Promise<SettingsResponse> {
  const { data } = await api.put<SettingsResponse>('/settings', values)
  return data
}

export async function resetSettings(): Promise<SettingsResponse> {
  const { data } = await api.post<SettingsResponse>('/settings/reset')
  return data
}
