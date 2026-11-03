import { isAxiosError } from 'axios'
import type { PredictionRecord } from '../types/prediction'
import type { ReviewRecord, ReviewRequest } from '../types/review'
import { api } from './api'

// The first prediction can take a few seconds, because the model has to warm up.
const PREDICT_TIMEOUT_MS = 60_000

export async function predictReport(reportId: string): Promise<PredictionRecord> {
  const { data } = await api.post<PredictionRecord>(
    `/reports/${encodeURIComponent(reportId)}/predict`,
    undefined,
    { timeout: PREDICT_TIMEOUT_MS },
  )
  return data
}

/** Returns the review of a prediction, or null when it has not been reviewed yet. */
export async function getPredictionReview(predictionId: string): Promise<ReviewRecord | null> {
  try {
    const { data } = await api.get<ReviewRecord>(`/predictions/${encodeURIComponent(predictionId)}/review`)
    return data
  } catch (error) {
    if (isAxiosError(error) && error.response?.status === 404) return null
    throw error
  }
}

export async function submitReview(predictionId: string, request: ReviewRequest): Promise<ReviewRecord> {
  const { data } = await api.post<ReviewRecord>(
    `/predictions/${encodeURIComponent(predictionId)}/review`,
    request,
  )
  return data
}
