import { useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import ErrorState from '../components/ErrorState'
import LoadingState from '../components/LoadingState'
import StatCard from '../components/StatCard'
import { useAsyncData } from '../hooks/useAsyncData'
import { DEFAULT_STEP_SIZE, STEP_SIZES, progressPercent } from '../lib/bulk'
import { formatNumber } from '../lib/format'
import { errorMessage } from '../services/api'
import { getBulkStatus, runBulkPredict } from '../services/bulk'

interface Progress {
  predicted: number
  needsReview: number
  target: number
}

function plural(count: number, one: string, many: string): string {
  return count === 1 ? one : many
}

export default function BulkPredictPage() {
  const status = useAsyncData(getBulkStatus)
  const [stepSize, setStepSize] = useState(DEFAULT_STEP_SIZE)
  const [running, setRunning] = useState(false)
  const [stopping, setStopping] = useState(false)
  const [progress, setProgress] = useState<Progress | null>(null)
  const [outcome, setOutcome] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const stopRequested = useRef(false)

  const unpredicted = status.data?.unpredicted ?? 0

  async function handleStart() {
    const target = unpredicted
    stopRequested.current = false
    setRunning(true)
    setStopping(false)
    setError(null)
    setOutcome(null)
    setProgress({ predicted: 0, needsReview: 0, target })

    let predicted = 0
    let needsReview = 0
    let remaining = target
    let stopped = false
    try {
      let keepGoing = true
      while (keepGoing) {
        const result = await runBulkPredict(stepSize)
        predicted += result.predicted
        needsReview += result.needs_review
        remaining = result.remaining
        setProgress({ predicted, needsReview, target })
        if (result.predicted === 0 || result.remaining === 0) {
          keepGoing = false
        } else if (stopRequested.current) {
          stopped = true
          keepGoing = false
        }
      }
      setOutcome(
        `${stopped ? 'Stopped after the current batch. ' : ''}` +
          `Predicted ${formatNumber(predicted)} ${plural(predicted, 'report', 'reports')}. ` +
          `${formatNumber(needsReview)} of them need review. ` +
          `${formatNumber(remaining)} ${plural(remaining, 'report is', 'reports are')} still without a prediction.`,
      )
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      setRunning(false)
      setStopping(false)
      await status.reload()
    }
  }

  function handleStop() {
    stopRequested.current = true
    setStopping(true)
  }

  const percent = progress ? progressPercent(progress.predicted, progress.target) : 0

  return (
    <section>
      <h1 className="text-2xl font-semibold">Bulk predict</h1>
      <p className="mt-1 text-sm text-slate-600">
        Runs the severity model on every report that has no prediction yet. It works in steps, so you can follow the
        progress and stop at any time. Reports that already have a prediction are not touched. The backend must be
        started with the models loaded.
      </p>

      {status.loading && !status.data && <LoadingState label="Counting reports..." />}
      {status.error && <ErrorState message={status.error} onRetry={() => void status.reload()} />}

      {status.data && (
        <div className="mt-6 space-y-6">
          <div className="grid gap-4 sm:grid-cols-3">
            <StatCard title="Total reports" value={formatNumber(status.data.total_reports)} />
            <StatCard title="With a prediction" value={formatNumber(status.data.reports_with_predictions)} />
            <StatCard title="Without a prediction" value={formatNumber(status.data.unpredicted)} />
          </div>

          <div className="rounded-lg border border-slate-200 bg-white p-4">
            {unpredicted === 0 && !running ? (
              <p className="text-sm text-slate-700">Every report already has a prediction.</p>
            ) : (
              <p className="text-sm text-slate-600">
                A prediction with a small margin is marked Needs review. Those predictions also appear in Pending
                reviews on the dashboard.
              </p>
            )}

            <div className="mt-4 flex flex-wrap items-end gap-3">
              <div>
                <label htmlFor="step-size" className="block text-sm font-medium text-slate-700">
                  Reports per step
                </label>
                <select
                  id="step-size"
                  value={stepSize}
                  disabled={running}
                  onChange={(event) => setStepSize(Number(event.target.value))}
                  className="mt-1 block rounded-md border border-slate-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50"
                >
                  {STEP_SIZES.map((size) => (
                    <option key={size} value={size}>
                      {size}
                    </option>
                  ))}
                </select>
              </div>
              <button
                type="button"
                onClick={() => void handleStart()}
                disabled={running || unpredicted === 0}
                className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:opacity-50"
              >
                {running ? 'Predicting...' : 'Predict all unpredicted reports'}
              </button>
              {running && (
                <button
                  type="button"
                  onClick={handleStop}
                  disabled={stopping}
                  className="rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50"
                >
                  {stopping ? 'Stopping...' : 'Stop'}
                </button>
              )}
              <button
                type="button"
                onClick={() => void status.reload()}
                disabled={running}
                className="rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50"
              >
                Refresh counts
              </button>
            </div>

            {progress && (
              <div className="mt-6">
                <div
                  role="progressbar"
                  aria-label="Prediction progress"
                  aria-valuemin={0}
                  aria-valuemax={progress.target}
                  aria-valuenow={progress.predicted}
                  className="h-3 w-full overflow-hidden rounded-full bg-slate-200"
                >
                  <div className="h-full rounded-full bg-indigo-600 transition-all" style={{ width: `${percent}%` }} />
                </div>
                <p className="mt-2 text-sm text-slate-700" aria-live="polite">
                  {`Predicted ${formatNumber(progress.predicted)} of ${formatNumber(progress.target)} reports (${percent}%). ${formatNumber(progress.needsReview)} need review.`}
                </p>
              </div>
            )}

            {outcome && (
              <p className="mt-4 rounded-md bg-emerald-50 p-3 text-sm text-emerald-900">{outcome}</p>
            )}
            {error && <ErrorState message={error} />}

            {outcome && (
              <div className="mt-4 flex flex-wrap gap-4 text-sm font-medium">
                <Link to="/" className="text-indigo-700 hover:underline">
                  View the dashboard
                </Link>
                <Link to="/reports" className="text-indigo-700 hover:underline">
                  Open the reports
                </Link>
              </div>
            )}
          </div>
        </div>
      )}
    </section>
  )
}
