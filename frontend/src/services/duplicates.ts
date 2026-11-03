import type { QueueQuery } from '../lib/duplicateQueue'
import type { FindResponse, QueueResponse, ReviewDecision, Suggestion } from '../types/duplicates'
import { api } from './api'

// The first search can take a few seconds, because the model has to warm up.
const FIND_TIMEOUT_MS = 60_000

export async function findDuplicates(
  reportId: string,
  options: { top_k: number; threshold: number },
): Promise<FindResponse> {
  const { data } = await api.post<FindResponse>(
    `/reports/${encodeURIComponent(reportId)}/duplicates/find`,
    options,
    { timeout: FIND_TIMEOUT_MS },
  )
  return data
}

export async function getReportDuplicates(reportId: string): Promise<Suggestion[]> {
  const { data } = await api.get<Suggestion[]>(`/reports/${encodeURIComponent(reportId)}/duplicates`)
  return data
}

export async function reviewSuggestion(
  suggestionId: string,
  decision: ReviewDecision,
  note?: string,
): Promise<Suggestion> {
  const body = note ? { decision, note } : { decision }
  const { data } = await api.post<Suggestion>(
    `/duplicate-suggestions/${encodeURIComponent(suggestionId)}/review`,
    body,
  )
  return data
}

export async function getSuggestions(query: QueueQuery): Promise<QueueResponse> {
  const params = { status: query.status, page: query.page, page_size: query.pageSize }
  const { data } = await api.get<QueueResponse>('/duplicate-suggestions', { params })
  return data
}
