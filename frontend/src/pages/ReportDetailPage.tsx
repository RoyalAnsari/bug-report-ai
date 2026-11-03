import { useCallback, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import DuplicatesSection from '../components/DuplicatesSection'
import EmptyState from '../components/EmptyState'
import ErrorState from '../components/ErrorState'
import LoadingState from '../components/LoadingState'
import ReviewPanel from '../components/ReviewPanel'
import SeverityBadge from '../components/SeverityBadge'
import { useAsyncData } from '../hooks/useAsyncData'
import { formatDateTime } from '../lib/format'
import { errorMessage } from '../services/api'
import { predictReport } from '../services/predictions'
import { getReport, getReportPredictions } from '../services/reports'

export default function ReportDetailPage() {
  const { reportId = '' } = useParams()
  const loadReport = useCallback(() => getReport(reportId), [reportId])
  const loadPredictions = useCallback(() => getReportPredictions(reportId), [reportId])
  const report = useAsyncData(loadReport)
  const predictions = useAsyncData(loadPredictions)
  const [predicting, setPredicting] = useState(false)
  const [predictError, setPredictError] = useState<string | null>(null)

  async function handlePredict() {
    setPredicting(true)
    setPredictError(null)
    try {
      await predictReport(reportId)
      await predictions.reload()
    } catch (e) {
      setPredictError(errorMessage(e))
    } finally {
      setPredicting(false)
    }
  }

  const latest = predictions.data && predictions.data.length > 0 ? predictions.data[0] : null

  return (
    <section>
      <Link to="/reports" className="text-sm font-medium text-indigo-700 hover:underline">
        Back to reports
      </Link>
      <h1 className="mt-3 text-2xl font-semibold">Report details</h1>

      {report.loading && !report.data && <LoadingState label="Loading the report..." />}
      {report.error && <ErrorState message={report.error} onRetry={() => void report.reload()} />}

      {report.data && (
        <div className="mt-6 space-y-6">
          <div className="rounded-lg border border-slate-200 bg-white p-4">
            <h2 className="text-sm font-medium text-slate-600">Bug text</h2>
            <p className="mt-2 whitespace-pre-wrap text-slate-900">{report.data.text}</p>

            <dl className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              <div>
                <dt className="text-sm text-slate-600">Severity</dt>
                <dd className="mt-1">
                  {report.data.severity ? (
                    <SeverityBadge label={report.data.severity} />
                  ) : (
                    <span className="text-sm text-slate-500">Not labeled</span>
                  )}
                </dd>
              </div>
              <div>
                <dt className="text-sm text-slate-600">Project</dt>
                <dd className="mt-1 text-slate-900">{report.data.project ?? '-'}</dd>
              </div>
              <div>
                <dt className="text-sm text-slate-600">Bug ID</dt>
                <dd className="mt-1 text-slate-900">{report.data.external_id ?? '-'}</dd>
              </div>
              <div>
                <dt className="text-sm text-slate-600">Source</dt>
                <dd className="mt-1 break-all text-slate-900">{report.data.source ?? '-'}</dd>
              </div>
              <div>
                <dt className="text-sm text-slate-600">Added</dt>
                <dd className="mt-1 text-slate-900">{formatDateTime(report.data.created_at)}</dd>
              </div>
              <div>
                <dt className="text-sm text-slate-600">Last changed</dt>
                <dd className="mt-1 text-slate-900">{formatDateTime(report.data.updated_at)}</dd>
              </div>
            </dl>
          </div>

          <div className="rounded-lg border border-slate-200 bg-white p-4">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <h2 className="font-medium">Predictions</h2>
                <p className="mt-1 text-sm text-slate-600">
                  The margin is the gap between the best and the second best score. It is not a probability.
                </p>
              </div>
              <button
                type="button"
                onClick={() => void handlePredict()}
                disabled={predicting}
                className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:opacity-50"
              >
                {predicting ? 'Predicting...' : 'Predict severity'}
              </button>
            </div>
            <p className="mt-2 text-xs text-slate-500">The backend must be started with the models loaded.</p>

            {predictError && <ErrorState message={predictError} />}

            {predictions.loading && !predictions.data && <LoadingState label="Loading predictions..." />}
            {predictions.error && <ErrorState message={predictions.error} onRetry={() => void predictions.reload()} />}
            {predictions.data && predictions.data.length === 0 && (
              <EmptyState title="No predictions yet" message="This report has not been predicted." />
            )}

            {latest && (
              <div className="mt-4">
                <ReviewPanel key={latest.id} prediction={latest} onReviewed={() => void report.reload()} />
              </div>
            )}

            {predictions.data && predictions.data.length > 0 && (
              <ul className="mt-4 divide-y divide-slate-100">
                {predictions.data.map((prediction) => (
                  <li key={prediction.id} className="flex flex-wrap items-center gap-x-4 gap-y-2 py-3 text-sm">
                    <SeverityBadge label={prediction.label} />
                    <span>{`Margin: ${prediction.margin}`}</span>
                    {prediction.needs_review && (
                      <span className="rounded-full bg-amber-100 px-2.5 py-1 text-xs font-medium text-amber-800">
                        Needs review
                      </span>
                    )}
                    <span className="text-slate-600">{`Model: ${prediction.model_version}`}</span>
                    <span className="text-slate-600">{formatDateTime(prediction.created_at)}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>

          <DuplicatesSection reportId={report.data.id} />
        </div>
      )}
    </section>
  )
}
