import type { ColumnMapping, ImportResult, UploadPreview } from '../types/upload'
import { api } from './api'

// Big files can take longer than the normal 15 seconds.
const UPLOAD_TIMEOUT_MS = 120_000

function buildForm(file: File, mapping?: ColumnMapping | null): FormData {
  const form = new FormData()
  form.append('file', file)
  if (mapping) form.append('mapping', JSON.stringify(mapping))
  return form
}

export async function previewUpload(file: File, mapping?: ColumnMapping | null): Promise<UploadPreview> {
  const { data } = await api.post<UploadPreview>('/uploads/preview', buildForm(file, mapping), {
    timeout: UPLOAD_TIMEOUT_MS,
  })
  return data
}

export async function importUpload(file: File, mapping?: ColumnMapping | null): Promise<ImportResult> {
  const { data } = await api.post<ImportResult>('/uploads/import', buildForm(file, mapping), {
    timeout: UPLOAD_TIMEOUT_MS,
  })
  return data
}
