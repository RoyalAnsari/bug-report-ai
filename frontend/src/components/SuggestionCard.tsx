import { useState } from 'react'
import { Link } from 'react-router-dom'
import { formatSimilarity } from '../lib/similarity'
import { errorMessage } from '../services/api'
import { reviewSuggestion } from '../services/duplicates'
import type { ReviewDecision, Suggestion } from '../types/duplicates'
import ErrorState from './ErrorState'

interface Props {
  suggestion: Suggestion
  /** Give this to also show the report the candidate belongs to (the review queue does this). */
  report?: { text: string | null; project: string | null }
  onChanged: () => void
}

const STATUS_STYLES: Record<string, { label: string; className: string }> = {
  pending: { label: 'Pending', className: 'bg-amber-100 text-amber-800' },
  confirmed: { label: 'Confirmed duplicate', className: 'bg-emerald-100 text-emerald-800' },
  rejected: { label: 'Rejected', className: 'bg-slate-200 text-slate-700' },
}

const buttonBase =
  'rounded-md px-3 py-1.5 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:opacity-50'

export default function SuggestionCard({ suggestion, report, onChanged }: Props) {
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function decide(decision: ReviewDecision) {
    setSaving(true)
    setError(null)
    try {
      await reviewSuggestion(suggestion.id, decision)
      onChanged()
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      setSaving(false)
    }
  }

  const status = STATUS_STYLES[suggestion.status] ?? {
    label: suggestion.status,
    className: 'bg-slate-100 text-slate-700',
  }
  const headingClass = 'text-xs font-medium uppercase tracking-wide text-slate-500'

  return (
    <article
      aria-label={`Suggestion for bug ${suggestion.candidate_id}`}
      className="rounded-lg border border-slate-200 bg-white p-4"
    >
      <div className={report ? 'grid gap-4 md:grid-cols-2' : ''}>
        {report && (
          <div>
            <h3 className={headingClass}>Report</h3>
            <p className="mt-1 text-slate-900">{report.text ?? 'The text of this report is not available.'}</p>
            <p className="mt-1 text-xs text-slate-600">{report.project ?? '-'}</p>
            <Link
              to={`/reports/${suggestion.report_id}`}
              className="mt-1 inline-block text-sm font-medium text-indigo-700 hover:underline"
            >
              Open report
            </Link>
          </div>
        )}
        <div>
          <h3 className={headingClass}>Possible duplicate</h3>
          <p className="mt-1 text-slate-900">{suggestion.candidate_text}</p>
          <p className="mt-1 text-xs text-slate-600">
            {`Bug ID ${suggestion.candidate_id}${suggestion.candidate_project ? ` · ${suggestion.candidate_project}` : ''}`}
          </p>
        </div>
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-3 border-t border-slate-100 pt-3">
        <span className="text-sm font-medium text-slate-900">{`Similarity: ${formatSimilarity(suggestion.similarity)}`}</span>
        <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${status.className}`}>{status.label}</span>
        {suggestion.status === 'pending' && (
          <div className="ml-auto flex gap-2">
            <button
              type="button"
              disabled={saving}
              onClick={() => void decide('confirm')}
              className={`${buttonBase} bg-indigo-600 text-white hover:bg-indigo-700`}
            >
              Confirm duplicate
            </button>
            <button
              type="button"
              disabled={saving}
              onClick={() => void decide('reject')}
              className={`${buttonBase} border border-slate-300 bg-white text-slate-700 hover:bg-slate-100`}
            >
              Reject
            </button>
          </div>
        )}
      </div>

      {error && <ErrorState message={error} />}
    </article>
  )
}
