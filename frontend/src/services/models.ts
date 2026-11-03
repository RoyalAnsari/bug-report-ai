import type { ModelDetail, ModelSummary } from '../types/models'
import { api } from './api'

export async function getModels(): Promise<ModelSummary[]> {
  const { data } = await api.get<ModelSummary[]>('/models')
  return data
}

export async function getModel(name: string, version: string): Promise<ModelDetail> {
  const { data } = await api.get<ModelDetail>(`/models/${encodeURIComponent(name)}/${encodeURIComponent(version)}`)
  return data
}
