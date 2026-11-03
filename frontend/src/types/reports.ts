export interface ReportItem {
  id: string
  text: string
  project: string | null
  severity: string | null
  external_id: string | null
  source: string | null
  created_at: string | null
  updated_at: string | null
}

export interface ReportListResponse {
  items: ReportItem[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface ReportQuery {
  page: number
  pageSize: number
  search: string
  project: string
  severity: string
  sort: string
}
