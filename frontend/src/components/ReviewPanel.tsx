import { useCallback, useState } from 'react'
import { useAsyncData } from '../hooks/useAsyncData'
import { formatDateTime } from '../lib/format'
import { SEVERITY_ORDER } from '../lib/severity'
import { errorMessage } from '../services/api'
import { getPredictionReview, submitReview } from '../services/predictions'
import type { PredictionRecord } from '../types/prediction'
import type { ReviewRecord, ReviewRequest } from '../types/review'
import ErrorState from './ErrorState'
import LoadingState from './LoadingState'
import SeverityBadge from './SeverityBadge'

interface Props {
  prediction: PredictionRecord
  onReviewed: () => void
}

const buttonBase =
  'rounded-md px-4 py-2 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:opacity-50'

export default function ReviewPanel({ prediction, onReviewed }: Props) {
  const loadReview = useCallback(() => getPredictionReview(prediction.id), [prediction.id])
  const existing = useAsyncData(loadReview)
  const [saved, setSaved] = useState<ReviewRecord | null>(null)
  const [label, setLabel] = useState('')
  const [note, setNote] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const review = saved ?? existing.data

  async function submit(request: ReviewRequest) {
    setSaving(true)
    setError(null)
    const trimmed = note.trim()
    try {
      const result = await submitReview(prediction.id, trimmed ? { ...request, note: trimmed } : request)
      setSaved(result)
      onReviewed()
    } catch (e) {
      setError(errorMessage(e))
      // If the prediction was reviewed in the meantime, show that review.
      void existing.reload()
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="rounded-md border border-slate-200 bg-slate-50 p-4">
      <h3 className="font-medium">Review the latest prediction</h3>

      {existing.loading && !review && <LoadingState label="Checking for a review..." />}
      {existing.error && <ErrorState message={existing.error} onRetry={() => void existing.reload()} />}

      {review && (
        <div className="mt-3 rounded-md bg-emerald-50 p-3 text-sm text-emerald-900">
          <p className="font-medium">{review.action === 'confirm' ? 'Prediction confirmed' : 'Prediction corrected'}</p>
          <p className="mt-2 flex flex-wrap items-center gap-2">
            <span>Final severity:</span>
            <SeverityBadge label={review.final_label} />
            <span>{`(predicted: ${review.predicted_label})`}</span>
          </p>
          {review.note && <p className="mt-2">{`Note: ${review.note}`}</p>}
          <p className="mt-2 text-xs">{`Reviewed ${formatDateTime(review.created_at)}`}</p>
        </div>
      )}

      {!review && !existing.loading && !existing.error && (
        <div className="mt-3">
          <p className="flex flex-wrap items-center gap-2 text-sm text-slate-700">
            <span>The model predicted:</span>
            <SeverityBadge label={prediction.label} />
          </p>

          <label htmlFor="review-note" className="mt-4 block text-sm font-medium text-slate-700">
            Note (optional)
          </label>
          <textarea
            id="review-note"
            value={note}
            maxLength={500}
            rows={2}
            onChange={(event) => setNote(event.target.value)}
            className="mt-1 block w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />

          <div className="mt-4 flex flex-wrap items-end gap-3">
            <button
              type="button"
              disabled={saving}
              onClick={() => void submit({ action: 'confirm' })}
              className={`${buttonBase} bg-indigo-600 text-white hover:bg-indigo-700`}
            >
              Confirm prediction
            </button>

            <div>
              <label htmlFor="review-label" className="block text-sm font-medium text-slate-700">
                Or choose the right severity
              </label>
              <select
                id="review-label"
                value={label}
                onChange={(event) => setLabel(event.target.value)}
                className="mt-1 block rounded-md border border-slate-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="">Choose a severity</option>
                {SEVERITY_ORDER.map((name) => (
                  <option key={name} value={name}>
                    {name}
                  </option>
                ))}
              </select>
            </div>
            <button
              type="button"
              disabled={saving || !label}
              onClick={() => void submit({ action: 'correct', label })}
              className={`${buttonBase} border border-slate-300 bg-white text-slate-700 hover:bg-slate-100`}
            >
              Save correction
            </button>
          </div>
        </div>
      )}

      {error && <ErrorState message={error} />}
    </div>
  )
}
