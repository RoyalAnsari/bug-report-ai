import { sortParams } from '../lib/reportQuery'
import type { PredictionRecord } from '../types/prediction'
import type { ReportItem, ReportListResponse, ReportQuery } from '../types/reports'
import { api } from './api'

export async function getReports(query: ReportQuery): Promise<ReportListResponse> {
  const { sortBy, order } = sortParams(query.sort)
  const params = {
    page: query.page,
    page_size: query.pageSize,
    search: query.search || undefined,
    project: query.project || undefined,
    severity: query.severity || undefined,
    sort_by: sortBy,
    order,
  }
  const { data } = await api.get<ReportListResponse>('/reports', { params })
  return data
}

export async function getProjects(): Promise<string[]> {
  const { data } = await api.get<{ projects: string[] }>('/reports/projects')
  return data.projects
}

export async function getReport(reportId: string): Promise<ReportItem> {
  const { data } = await api.get<ReportItem>(`/reports/${encodeURIComponent(reportId)}`)
  return data
}

export async function getReportPredictions(reportId: string): Promise<PredictionRecord[]> {
  const { data } = await api.get<PredictionRecord[]>(`/reports/${encodeURIComponent(reportId)}/predictions`)
  return data
}
