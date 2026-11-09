import { useState } from 'react'
import type { ChangeEvent, FormEvent } from 'react'
import { errorMessage } from '../services/api'
import { evaluateCsv } from '../services/triage'
import type { EvaluationResult } from '../types/triage'

function percent(value: number): string {
  return `${(value * 100).toFixed(1)}%`
}

export default function EvaluatePage() {
  const [file, setFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<EvaluationResult | null>(null)

  function handleFile(event: ChangeEvent<HTMLInputElement>) {
    setFile(event.target.files?.[0] ?? null)
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!file || loading) return
    setLoading(true)
    setError(null)
    try {
      setResult(await evaluateCsv(file))
    } catch (problem) {
      setResult(null)
      setError(errorMessage(problem))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-4xl space-y-6">
      <div>
        <h1 className="text-xl font-semibold">Evaluate on your own labelled bugs</h1>
        <p className="mt-1 text-sm text-slate-600">
          Upload a CSV with a text column (text, title, summary or short description) and the true severity (severity or
          label). The model predicts each report and you see how often it is right. Up to 1,000 rows and 2 MB. Nothing is
          saved.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4 rounded-lg border border-slate-200 bg-white p-4">
        <div>
          <label htmlFor="evaluate-file" className="mb-1 block text-sm font-medium text-slate-700">
            CSV file
          </label>
          <input id="evaluate-file" type="file" accept=".csv,text/csv" onChange={handleFile} className="text-sm" />
        </div>
        <button
          type="submit"
          disabled={!file || loading}
          className="rounded-md bg-indigo-600 px-3 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-60"
        >
          {loading ? 'Evaluating...' : 'Evaluate'}
        </button>
        {loading && <p className="text-sm text-slate-600">This can take up to a minute for a large file.</p>}
      </form>

      {error && (
        <p role="alert" className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">
          {error}
        </p>
      )}

      {result && (
        <div className="space-y-4">
          <section className="grid gap-3 sm:grid-cols-4">
            <div className="rounded-lg border border-slate-200 bg-white p-3">
              <div className="text-xs text-slate-500">Reports used</div>
              <div className="text-xl font-semibold" data-testid="rows-used">{result.rows_used}</div>
              <div className="text-xs text-slate-500">{result.rows_skipped} skipped</div>
            </div>
            <div className="rounded-lg border border-slate-200 bg-white p-3">
              <div className="text-xs text-slate-500">Accuracy</div>
              <div className="text-xl font-semibold" data-testid="accuracy">{percent(result.accuracy)}</div>
            </div>
            <div className="rounded-lg border border-slate-200 bg-white p-3">
              <div className="text-xs text-slate-500">Macro F1</div>
              <div className="text-xl font-semibold" data-testid="macro-f1">{result.macro_f1.toFixed(3)}</div>
            </div>
            <div className="rounded-lg border border-slate-200 bg-white p-3">
              <div className="text-xs text-slate-500">Always guessing the most common class</div>
              <div className="text-xl font-semibold">{percent(result.majority_baseline_accuracy)}</div>
              <div className="text-xs text-slate-500">accuracy</div>
            </div>
          </section>

          {result.warnings.length > 0 && (
            <ul className="space-y-1 rounded-md border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
              {result.warnings.map((warning) => (
                <li key={warning}>{warning}</li>
              ))}
            </ul>
          )}

          <section className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
            <table className="min-w-full text-left text-sm">
              <caption className="p-3 text-left text-sm font-semibold">Result for each severity</caption>
              <thead className="border-y border-slate-200 bg-slate-50 text-slate-600">
                <tr>
                  <th className="px-3 py-2 font-medium">Severity</th>
                  <th className="px-3 py-2 font-medium">Precision</th>
                  <th className="px-3 py-2 font-medium">Recall</th>
                  <th className="px-3 py-2 font-medium">F1</th>
                  <th className="px-3 py-2 font-medium">Reports</th>
                </tr>
              </thead>
              <tbody>
                {result.per_class.map((row) => (
                  <tr key={row.label} className="border-b border-slate-100 last:border-0">
                    <td className="px-3 py-2 capitalize">{row.label}</td>
                    <td className="px-3 py-2 tabular-nums">{row.precision.toFixed(2)}</td>
                    <td className="px-3 py-2 tabular-nums">{row.recall.toFixed(2)}</td>
                    <td className="px-3 py-2 tabular-nums">{row.f1.toFixed(2)}</td>
                    <td className="px-3 py-2 tabular-nums">{row.support}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>

          <section className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
            <table className="min-w-full text-left text-sm">
              <caption className="p-3 text-left text-sm font-semibold">
                Confusion matrix (rows: true severity, columns: predicted)
              </caption>
              <thead className="border-y border-slate-200 bg-slate-50 text-slate-600">
                <tr>
                  <th className="px-3 py-2 font-medium">True \ predicted</th>
                  {result.labels.map((label) => (
                    <th key={label} className="px-3 py-2 font-medium capitalize">
                      {label}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {result.confusion_matrix.map((row, rowIndex) => (
                  <tr key={result.labels[rowIndex]} className="border-b border-slate-100 last:border-0">
                    <th className="px-3 py-2 font-medium capitalize">{result.labels[rowIndex]}</th>
                    {row.map((value, columnIndex) => (
                      <td
                        key={result.labels[columnIndex]}
                        className={`px-3 py-2 tabular-nums ${rowIndex === columnIndex ? 'bg-indigo-50 font-semibold' : ''}`}
                      >
                        {value}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </section>

          {result.skipped_examples.length > 0 && (
            <div className="text-sm text-slate-600">
              <p className="font-medium">Some rows were skipped, for example:</p>
              <ul className="list-disc pl-5">
                {result.skipped_examples.map((example) => (
                  <li key={example}>{example}</li>
                ))}
              </ul>
            </div>
          )}

          <p className="text-xs text-slate-500">Model: {result.model_version}.</p>
        </div>
      )}
    </div>
  )
}
