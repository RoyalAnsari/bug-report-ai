export type FieldName = 'text' | 'severity' | 'project' | 'external_id'

export type ColumnMapping = Record<FieldName, string | null>

export interface RowError {
  row: number
  message: string
}

export interface UploadPreview {
  filename: string
  encoding: string
  headers: string[]
  mapping: ColumnMapping
  needs_mapping: boolean
  preview: Record<string, string>[]
  total_rows: number
  valid_rows: number
  error_count: number
  errors: RowError[]
  errors_truncated: boolean
}

export interface ImportResult {
  total_rows: number
  valid_rows: number
  error_count: number
  errors: RowError[]
  errors_truncated: boolean
  inserted: number
  already_existed: number
  merged_duplicates: number
}
