export interface BulkStatus {
  total_reports: number
  reports_with_predictions: number
  unpredicted: number
}

export interface BulkResult {
  requested: number
  predicted: number
  needs_review: number
  remaining: number
  model_version: string
  note: string
}
