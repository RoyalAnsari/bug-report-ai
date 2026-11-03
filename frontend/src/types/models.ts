export interface ClassMetrics {
  precision: number
  recall: number
  f1: number
  support: number
}

export interface Evaluation {
  split: string
  macro_f1: number
  macro_precision: number | null
  macro_recall: number | null
  per_class: Record<string, ClassMetrics>
  confusion_matrix: number[][]
  labels_order: string[]
  rows: number
}

export interface TrainingInfo {
  seed?: number | null
  resample_target?: number | null
  validation_macro_f1?: number | null
  library_versions?: Record<string, string> | null
}

export interface ModelSummary {
  id: string
  name: string
  version: string
  task: string
  has_evaluation: boolean
  macro_f1: number | null
  created_at: string | null
}

export interface ModelDetail {
  id: string
  name: string
  version: string
  task: string
  algorithm: string
  variant: string | null
  uses_offsets: boolean | null
  labels: string[] | null
  artifact_path: string | null
  training: TrainingInfo | null
  evaluation: Evaluation | null
  evaluation_note: string | null
  config: Record<string, unknown> | null
  created_at: string | null
  updated_at: string | null
}
