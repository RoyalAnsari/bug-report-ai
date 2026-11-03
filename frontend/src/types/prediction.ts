export interface PredictionRecord {
  id: string
  report_id: string
  label: string
  margin: number
  needs_review: boolean
  scores: Record<string, number>
  model_version: string
  created_at: string | null
  note: string
}
