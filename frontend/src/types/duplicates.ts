export type ReviewDecision = 'confirm' | 'reject'

export interface Suggestion {
  id: string
  report_id: string
  candidate_id: string
  candidate_text: string
  candidate_project: string | null
  similarity: number
  score_type: string
  status: string
  created_at: string | null
}

export interface QueueItem extends Suggestion {
  report_text: string | null
  report_project: string | null
}

export interface QueueResponse {
  items: QueueItem[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface FindResponse {
  report_id: string
  threshold: number
  found: number
  new: number
  suggestions: Suggestion[]
}
