import type { DashboardSummary } from '../types/dashboard'
import { api } from './api'

export async function getDashboardSummary(): Promise<DashboardSummary> {
  const { data } = await api.get<DashboardSummary>('/dashboard/summary')
  return data
}
