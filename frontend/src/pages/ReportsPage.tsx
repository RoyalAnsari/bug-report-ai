import { useCallback, useMemo } from 'react'
import { useSearchParams } from 'react-router-dom'
import EmptyState from '../components/EmptyState'
import ErrorState from '../components/ErrorState'
import LoadingState from '../components/LoadingState'
import Pagination from '../components/Pagination'
import ReportFilters from '../components/ReportFilters'
import ReportsTable from '../components/ReportsTable'
import { useAsyncData } from '../hooks/useAsyncData'
import { DEFAULT_QUERY, parseQuery, toSearchParams } from '../lib/reportQuery'
import { getProjects, getReports } from '../services/reports'
import type { ReportQuery } from '../types/reports'

export default function ReportsPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const query = useMemo(() => parseQuery(searchParams), [searchParams])

  const fetchReports = useCallback(() => getReports(query), [query])
  const reports = useAsyncData(fetchReports)
  const projects = useAsyncData(getProjects)

  // Changing a filter always goes back to page 1.
  function update(patch: Partial<ReportQuery>) {
    setSearchParams(toSearchParams({ ...query, page: 1, ...patch }))
  }

  function goToPage(page: number) {
    setSearchParams(toSearchParams({ ...query, page }))
  }

  function clearFilters() {
    setSearchParams(toSearchParams({ ...DEFAULT_QUERY, sort: query.sort, pageSize: query.pageSize }))
  }

  const data = reports.data

  return (
    <section>
      <h1 className="text-2xl font-semibold">Reports</h1>
      <p className="mt-1 text-sm text-slate-600">
        Search and filter the bug reports. Search matches whole words, not parts of a word.
      </p>

      <div className="mt-6">
        <ReportFilters query={query} projects={projects.data ?? []} onChange={update} onClear={clearFilters} />
      </div>

      {reports.loading && !data && <LoadingState label="Loading reports..." />}
      {reports.error && <ErrorState message={reports.error} onRetry={() => void reports.reload()} />}

      {data && data.items.length === 0 && data.total === 0 && (
        <EmptyState title="No reports match your filters" message="Try a different search, or clear the filters." />
      )}

      {data && data.items.length === 0 && data.total > 0 && (
        <div className="mt-6">
          <EmptyState title="There are no reports on this page" message="Go back to the first page." />
          <button
            type="button"
            onClick={() => goToPage(1)}
            className="mt-3 rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-100"
          >
            Go to page 1
          </button>
        </div>
      )}

      {data && data.items.length > 0 && (
        <div className="mt-6" aria-busy={reports.loading}>
          <ReportsTable reports={data.items} />
          <Pagination
            page={data.page}
            pages={data.pages}
            pageSize={data.page_size}
            total={data.total}
            onPageChange={goToPage}
            disabled={reports.loading}
          />
        </div>
      )}
    </section>
  )
}
