export interface TriageRequest {
  text: string
  project?: string | null
  top_k?: number
}

export interface TriageSeverity {
  label: string
  margin: number
  needs_review: boolean
  scores: Record<string, number>
}

export interface SimilarReport {
  bug_id: number
  project: string
  text: string
  similarity: number
  likely_duplicate: boolean
}

export interface TriageResult {
  severity: TriageSeverity
  similar: SimilarReport[]
  model_version: string
  duplicate_threshold: number | null
}

export interface ClassMetric {
  label: string
  precision: number
  recall: number
  f1: number
  support: number
}

export interface EvaluationResult {
  model_version: string
  rows_used: number
  rows_skipped: number
  skipped_examples: string[]
  accuracy: number
  macro_f1: number
  majority_baseline_accuracy: number
  labels: string[]
  per_class: ClassMetric[]
  confusion_matrix: number[][]
  warnings: string[]
}
