export type ReviewAction = 'confirm' | 'correct'

export interface ReviewRequest {
  action: ReviewAction
  label?: string
  note?: string
}

export interface ReviewRecord {
  id: string
  prediction_id: string
  report_id: string
  action: string
  predicted_label: string
  final_label: string
  note: string | null
  created_at: string | null
}
