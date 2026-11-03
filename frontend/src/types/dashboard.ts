export interface DashboardSummary {
  total_reports: number
  severity_distribution: Record<string, number>
  predictions_total: number
  reports_with_predictions: number
  pending_reviews: number
  duplicate_suggestions: Record<string, number>
  duplicate_suggestions_total: number
}
