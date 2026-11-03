import EmptyState from '../components/EmptyState'
import ErrorState from '../components/ErrorState'
import LoadingState from '../components/LoadingState'
import SeverityBadge from '../components/SeverityBadge'
import SeverityChart from '../components/SeverityChart'
import StatCard from '../components/StatCard'
import { useAsyncData } from '../hooks/useAsyncData'
import { formatNumber } from '../lib/format'
import { toChartData } from '../lib/severity'
import { getDashboardSummary } from '../services/dashboard'
import type { DashboardSummary } from '../types/dashboard'

function DashboardContent({ data }: { data: DashboardSummary }) {
  const rows = toChartData(data.severity_distribution)
  const duplicates = data.duplicate_suggestions
  const duplicateHint =
    `${formatNumber(duplicates.pending ?? 0)} pending, ` +
    `${formatNumber(duplicates.confirmed ?? 0)} confirmed, ` +
    `${formatNumber(duplicates.rejected ?? 0)} rejected`

  return (
    <>
      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard title="Total reports" value={formatNumber(data.total_reports)} />
        <StatCard
          title="Reports with a prediction"
          value={formatNumber(data.reports_with_predictions)}
          hint={`of ${formatNumber(data.total_reports)} reports. ${formatNumber(data.predictions_total)} predictions saved in total.`}
        />
        <StatCard
          title="Pending reviews"
          value={formatNumber(data.pending_reviews)}
          hint="Latest prediction needs a human check"
        />
        <StatCard
          title="Duplicate suggestions"
          value={formatNumber(data.duplicate_suggestions_total)}
          hint={duplicateHint}
        />
      </div>

      <div className="mt-6 rounded-lg border border-slate-200 bg-white p-4">
        <h2 className="font-medium">Severity distribution</h2>
        <p className="mt-1 text-sm text-slate-600">Number of reports for each severity label.</p>
        <div className="mt-4">
          <SeverityChart data={rows} />
        </div>
        <ul className="mt-4 flex flex-wrap gap-x-6 gap-y-2" aria-label="Reports per severity">
          {rows.map((row) => (
            <li key={row.label} className="flex items-center gap-2 text-sm">
              <SeverityBadge label={row.label} />
              <span className="font-medium text-slate-900">{formatNumber(row.count)}</span>
            </li>
          ))}
        </ul>
      </div>
    </>
  )
}

export default function DashboardPage() {
  const { data, error, loading, reload } = useAsyncData(getDashboardSummary)

  return (
    <section>
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">Dashboard</h1>
          <p className="mt-1 text-sm text-slate-600">Counts from the bug reports stored in the database.</p>
        </div>
        <button
          type="button"
          onClick={() => void reload()}
          disabled={loading}
          className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50"
        >
          Refresh
        </button>
      </div>

      {loading && !data && <LoadingState label="Loading dashboard..." />}
      {error && <ErrorState message={error} onRetry={() => void reload()} />}
      {data && data.total_reports === 0 && (
        <EmptyState title="No bug reports yet" message="Reports will appear here once they are imported." />
      )}
      {data && data.total_reports > 0 && <DashboardContent data={data} />}
    </section>
  )
}
