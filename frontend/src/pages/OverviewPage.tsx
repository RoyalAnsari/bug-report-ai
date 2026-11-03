import ErrorState from '../components/ErrorState'
import LoadingState from '../components/LoadingState'
import StatusBadge from '../components/StatusBadge'
import { useHealth } from '../hooks/useHealth'

export default function OverviewPage() {
  const { data, error, loading, reload } = useHealth()

  return (
    <section>
      <h1 className="text-2xl font-semibold">System status</h1>
      <p className="mt-1 text-sm text-slate-600">Live status of the backend API and the loaded models.</p>

      <div className="mt-6 rounded-lg border border-slate-200 bg-white p-4">
        <div className="flex items-center justify-between">
          <h2 className="font-medium">Backend status</h2>
          <button
            type="button"
            onClick={() => void reload()}
            disabled={loading}
            className="rounded-md border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50"
          >
            Refresh
          </button>
        </div>

        {loading && <LoadingState label="Checking backend..." />}
        {error && <ErrorState message={error} onRetry={() => void reload()} />}
        {data && !loading && (
          <div className="mt-3 flex flex-wrap gap-2">
            <StatusBadge ok={data.status === 'ok'} label={`API: ${data.status}`} />
            <StatusBadge
              ok={data.models.severity_loaded}
              label={`Severity model: ${data.models.severity_loaded ? 'loaded' : 'not loaded'}`}
            />
            <StatusBadge
              ok={data.models.duplicates_loaded}
              label={`Duplicate model: ${data.models.duplicates_loaded ? 'loaded' : 'not loaded'}`}
            />
          </div>
        )}
      </div>
    </section>
  )
}
