import { useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import ErrorState from '../components/ErrorState'
import FileDropzone from '../components/FileDropzone'
import LoadingState from '../components/LoadingState'
import MappingForm from '../components/MappingForm'
import PreviewTable from '../components/PreviewTable'
import RowErrorList from '../components/RowErrorList'
import StatCard from '../components/StatCard'
import { formatNumber } from '../lib/format'
import { validateFile } from '../lib/upload'
import { errorMessage } from '../services/api'
import { importUpload, previewUpload } from '../services/upload'
import type { ColumnMapping, FieldName, ImportResult, UploadPreview } from '../types/upload'

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<UploadPreview | null>(null)
  const [mapping, setMapping] = useState<ColumnMapping | null>(null)
  const [result, setResult] = useState<ImportResult | null>(null)
  const [busy, setBusy] = useState<'preview' | 'import' | null>(null)
  const [error, setError] = useState<string | null>(null)
  // Only the newest preview request may change the screen.
  const latestRequest = useRef(0)

  async function runPreview(selected: File, chosenMapping: ColumnMapping | null) {
    const requestId = ++latestRequest.current
    setBusy('preview')
    setError(null)
    try {
      const data = await previewUpload(selected, chosenMapping)
      if (requestId !== latestRequest.current) return
      setPreview(data)
      setMapping(data.mapping)
    } catch (e) {
      if (requestId !== latestRequest.current) return
      setError(errorMessage(e))
    } finally {
      if (requestId === latestRequest.current) setBusy(null)
    }
  }

  function handleFile(selected: File) {
    latestRequest.current += 1
    setResult(null)
    setPreview(null)
    setMapping(null)
    const problem = validateFile(selected)
    if (problem) {
      setFile(null)
      setBusy(null)
      setError(problem)
      return
    }
    setFile(selected)
    void runPreview(selected, null)
  }

  function handleMappingChange(field: FieldName, column: string | null) {
    if (!file || !mapping) return
    const next: ColumnMapping = { ...mapping, [field]: column }
    setMapping(next)
    void runPreview(file, next)
  }

  async function handleImport() {
    if (!file || !mapping) return
    setBusy('import')
    setError(null)
    try {
      setResult(await importUpload(file, mapping))
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      setBusy(null)
    }
  }

  function reset() {
    latestRequest.current += 1
    setFile(null)
    setPreview(null)
    setMapping(null)
    setResult(null)
    setError(null)
    setBusy(null)
  }

  const importLabel = preview
    ? `Import ${formatNumber(preview.valid_rows)} valid ${preview.valid_rows === 1 ? 'row' : 'rows'}`
    : 'Import'

  return (
    <section>
      <h1 className="text-2xl font-semibold">Upload bug reports</h1>
      <p className="mt-1 text-sm text-slate-600">
        Choose a CSV file, check the preview, then import it. Nothing is saved until you click Import.
      </p>

      {!result && (
        <div className="mt-6">
          <FileDropzone onFile={handleFile} disabled={busy !== null} />
        </div>
      )}

      {error && <ErrorState message={error} />}
      {busy === 'preview' && <LoadingState label="Checking the file..." />}

      {preview && !result && (
        <div className="mt-6 space-y-6">
          <div className="rounded-lg border border-slate-200 bg-white p-4">
            <p className="text-sm text-slate-600">
              File: <span className="font-medium text-slate-900">{preview.filename}</span> ({preview.encoding})
            </p>
            <div className="mt-4 grid gap-4 sm:grid-cols-3">
              <StatCard title="Rows in file" value={formatNumber(preview.total_rows)} />
              <StatCard title="Valid rows" value={formatNumber(preview.valid_rows)} />
              <StatCard title="Rows with problems" value={formatNumber(preview.error_count)} />
            </div>
            <RowErrorList errors={preview.errors} total={preview.error_count} truncated={preview.errors_truncated} />
          </div>

          <div className="rounded-lg border border-slate-200 bg-white p-4">
            <h2 className="font-medium">Match the columns</h2>
            <p className="mt-1 text-sm text-slate-600">
              Only the bug text is required. Rows without a severity are saved without a label. If a report is already
              in the database, a severity in this file replaces the saved one.
            </p>
            {preview.needs_mapping && (
              <p className="mt-3 rounded-md bg-amber-50 p-3 text-sm text-amber-900">
                Choose which column holds the bug text.
              </p>
            )}
            <div className="mt-4">
              <MappingForm
                headers={preview.headers}
                mapping={mapping ?? preview.mapping}
                onChange={handleMappingChange}
                disabled={busy !== null}
              />
            </div>
          </div>

          <div className="rounded-lg border border-slate-200 bg-white p-4">
            <h2 className="mb-3 font-medium">Preview of the first rows</h2>
            <PreviewTable headers={preview.headers} rows={preview.preview} />
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <button
              type="button"
              onClick={() => void handleImport()}
              disabled={busy !== null || preview.needs_mapping || preview.valid_rows === 0}
              className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:opacity-50"
            >
              {busy === 'import' ? 'Importing...' : importLabel}
            </button>
            <button
              type="button"
              onClick={reset}
              disabled={busy === 'import'}
              className="rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50"
            >
              Start over
            </button>
          </div>
        </div>
      )}

      {result && (
        <div className="mt-6 rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-emerald-900">
          <h2 className="font-medium">Import finished</h2>
          <dl className="mt-3 grid gap-3 sm:grid-cols-2">
            <div>
              <dt className="text-sm">New reports added</dt>
              <dd className="text-2xl font-semibold">{formatNumber(result.inserted)}</dd>
            </div>
            <div>
              <dt className="text-sm">Already in the database</dt>
              <dd className="text-2xl font-semibold">{formatNumber(result.already_existed)}</dd>
            </div>
            <div>
              <dt className="text-sm">Repeated inside the file</dt>
              <dd className="text-2xl font-semibold">{formatNumber(result.merged_duplicates)}</dd>
            </div>
            <div>
              <dt className="text-sm">Rows skipped because of problems</dt>
              <dd className="text-2xl font-semibold">{formatNumber(result.error_count)}</dd>
            </div>
          </dl>
          <div className="mt-4 flex flex-wrap items-center gap-4">
            <Link to="/" className="text-sm font-medium text-indigo-700 hover:underline">
              View the dashboard
            </Link>
            <button
              type="button"
              onClick={reset}
              className="rounded-md border border-emerald-300 bg-white px-3 py-1.5 text-sm font-medium text-emerald-900 hover:bg-emerald-100 focus:outline-none focus:ring-2 focus:ring-emerald-500"
            >
              Upload another file
            </button>
          </div>
        </div>
      )}
    </section>
  )
}
