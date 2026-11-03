import { useCallback, useMemo } from 'react'
import { useSearchParams } from 'react-router-dom'
import EmptyState from '../components/EmptyState'
import ErrorState from '../components/ErrorState'
import LoadingState from '../components/LoadingState'
import Pagination from '../components/Pagination'
import SuggestionCard from '../components/SuggestionCard'
import { useAsyncData } from '../hooks/useAsyncData'
import { QUEUE_STATUSES, parseQueueQuery, toQueueParams } from '../lib/duplicateQueue'
import type { QueueQuery } from '../lib/duplicateQueue'
import { getSuggestions } from '../services/duplicates'

export default function DuplicatesPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const query = useMemo(() => parseQueueQuery(searchParams), [searchParams])
  const fetchQueue = useCallback(() => getSuggestions(query), [query])
  const queue = useAsyncData(fetchQueue)

  function update(patch: Partial<QueueQuery>) {
    setSearchParams(toQueueParams({ ...query, ...patch }))
  }

  const data = queue.data

  return (
    <section>
      <h1 className="text-2xl font-semibold">Duplicate review</h1>
      <p className="mt-1 text-sm text-slate-600">
        Candidates found by the model. Similarity is a cosine similarity score, not a probability. Confirm or reject
        each one. To create candidates, open a report and use Find possible duplicates.
      </p>

      <div className="mt-6">
        <label htmlFor="queue-status" className="block text-sm font-medium text-slate-700">
          Status
        </label>
        <select
          id="queue-status"
          value={query.status}
          onChange={(event) => update({ status: event.target.value as QueueQuery['status'], page: 1 })}
          className="mt-1 block rounded-md border border-slate-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
        >
          {QUEUE_STATUSES.map((item) => (
            <option key={item.value} value={item.value}>
              {item.label}
            </option>
          ))}
        </select>
      </div>

      {queue.loading && !data && <LoadingState label="Loading suggestions..." />}
      {queue.error && <ErrorState message={queue.error} onRetry={() => void queue.reload()} />}

      {data && data.items.length === 0 && data.total === 0 && (
        <EmptyState
          title="No suggestions to review"
          message="Nothing matches this status. Open a report and use Find possible duplicates to create candidates."
        />
      )}

      {data && data.items.length === 0 && data.total > 0 && (
        <div className="mt-6">
          <EmptyState title="There are no suggestions on this page" message="Go back to the first page." />
          <button
            type="button"
            onClick={() => update({ page: 1 })}
            className="mt-3 rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-100"
          >
            Go to page 1
          </button>
        </div>
      )}

      {data && data.items.length > 0 && (
        <div className="mt-6" aria-busy={queue.loading}>
          <ul className="space-y-3">
            {data.items.map((item) => (
              <li key={item.id}>
                <SuggestionCard
                  suggestion={item}
                  report={{ text: item.report_text, project: item.report_project }}
                  onChanged={() => void queue.reload()}
                />
              </li>
            ))}
          </ul>
          <Pagination
            page={data.page}
            pages={data.pages}
            pageSize={data.page_size}
            total={data.total}
            noun="suggestions"
            onPageChange={(page) => update({ page })}
            disabled={queue.loading}
          />
        </div>
      )}
    </section>
  )
}
