import type { FieldName } from '../types/upload'

// Same limit as the backend (5 MB). The backend checks again.
export const MAX_UPLOAD_BYTES = 5 * 1024 * 1024

export const FIELD_ORDER: FieldName[] = ['text', 'severity', 'project', 'external_id']

export const FIELD_LABELS: Record<FieldName, string> = {
  text: 'Bug text (required)',
  severity: 'Severity',
  project: 'Project',
  external_id: 'Bug ID',
}

/** Returns a message when the file cannot be used, or null when it looks fine. */
export function validateFile(file: File): string | null {
  if (!file.name.toLowerCase().endsWith('.csv')) return 'Only .csv files are accepted'
  if (file.size === 0) return 'File is empty'
  if (file.size > MAX_UPLOAD_BYTES) return 'File is too large (limit is 5 MB)'
  return null
}
