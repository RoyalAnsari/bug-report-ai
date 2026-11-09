import type { EvaluationResult, TriageRequest, TriageResult } from '../types/triage'
import { api } from './api'

export async function triageReport(payload: TriageRequest): Promise<TriageResult> {
  const { data } = await api.post<TriageResult>('/triage', payload)
  return data
}

export async function evaluateCsv(file: File): Promise<EvaluationResult> {
  const form = new FormData()
  form.append('file', file)
  // Is mein model hazaar tak reports par chalta hai, is liye normal se lamba intezar.
  const { data } = await api.post<EvaluationResult>('/evaluate', form, { timeout: 180000 })
  return data
}
