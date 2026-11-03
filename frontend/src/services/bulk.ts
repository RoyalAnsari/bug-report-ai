import type { BulkResult, BulkStatus } from '../types/bulk'
import { api } from './api'

// A step can take a while on a slow laptop.
const BULK_TIMEOUT_MS = 120_000

export async function getBulkStatus(): Promise<BulkStatus> {
  const { data } = await api.get<BulkStatus>('/predictions/bulk/status')
  return data
}

export async function runBulkPredict(limit: number): Promise<BulkResult> {
  const { data } = await api.post<BulkResult>('/predictions/bulk', { limit }, { timeout: BULK_TIMEOUT_MS })
  return data
}
