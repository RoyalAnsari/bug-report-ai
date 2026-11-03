import { useCallback, useState } from 'react'
import { useAsyncData } from '../hooks/useAsyncData'
import { DEFAULT_THRESHOLD, DEFAULT_TOP_K, THRESHOLD_OPTIONS, TOP_K_OPTIONS } from '../lib/similarity'
import { errorMessage } from '../services/api'
import { findDuplicates, getReportDuplicates } from '../services/duplicates'
import { getSettings } from '../services/settings'
import EmptyState from './EmptyState'
import ErrorState from './ErrorState'
import LoadingState from './LoadingState'
import SuggestionCard from './SuggestionCard'

interface Props {
  reportId: string
}

const selectClass =
  'mt-1 block rounded-md border border-slate-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500'

function withValue(options: number[], value: number): number[] {
  return Array.from(new Set([...options, value])).sort((a, b) => a - b)
}

export default function DuplicatesSection({ reportId }: Props) {
  const loadList = useCallback(() => getReportDuplicates(reportId), [reportId])
  const list = useAsyncData(loadList)
  // The two boxes start from the saved settings. If they cannot be loaded, the built-in defaults are used.
  const settings = useAsyncData(getSettings)
  const [chosenThreshold, setChosenThreshold] = useState<number | null>(null)
  const [chosenTopK, setChosenTopK] = useState<number | null>(null)
  const [finding, setFinding] = useState(false)
  const [findError, setFindError] = useState<string | null>(null)
  const [summary, setSummary] = useState<string | null>(null)

  const threshold = chosenThreshold ?? settings.data?.values.duplicate_threshold ?? DEFAULT_THRESHOLD
  const topK = chosenTopK ?? settings.data?.values.duplicate_top_k ?? DEFAULT_TOP_K

  async function handleFind() {
    setFinding(true)
    setFindError(null)
    setSummary(null)
    try {
      const result = await findDuplicates(reportId, { top_k: topK, threshold })
      setSummary(
        result.found === 0
          ? `No candidates reached a similarity of ${result.threshold.toFixed(2)}. Try a lower minimum similarity.`
          : `Found ${result.found} possible ${result.found === 1 ? 'duplicate' : 'duplicates'}, ${result.new} new.`,
      )
      await list.reload()
    } catch (e) {
      setFindError(errorMessage(e))
    } finally {
      setFinding(false)
    }
  }

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4">
      <h2 className="font-medium">Possible duplicates</h2>
      <p className="mt-1 text-sm text-slate-600">
        Similarity is the cosine similarity between text embeddings. It is a score, not a probability. The starting
        values come from the Settings page and have not been tested against labelled duplicates, so a person has to
        confirm each candidate.
      </p>

      <div className="mt-4 flex flex-wrap items-end gap-3">
        <div>
          <label htmlFor="dup-threshold" className="block text-sm font-medium text-slate-700">
            Minimum similarity
          </label>
          <select
            id="dup-threshold"
            value={threshold}
            onChange={(event) => setChosenThreshold(Number(event.target.value))}
            className={selectClass}
          >
            {withValue(THRESHOLD_OPTIONS, threshold).map((value) => (
              <option key={value} value={value}>
                {value.toFixed(2)}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="dup-top-k" className="block text-sm font-medium text-slate-700">
            Candidates to show
          </label>
          <select
            id="dup-top-k"
            value={topK}
            onChange={(event) => setChosenTopK(Number(event.target.value))}
            className={selectClass}
          >
            {withValue(TOP_K_OPTIONS, topK).map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
        </div>
        <button
          type="button"
          onClick={() => void handleFind()}
          disabled={finding}
          className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:opacity-50"
        >
          {finding ? 'Searching...' : 'Find possible duplicates'}
        </button>
      </div>

      {summary && (
        <p className="mt-3 text-sm text-slate-700" aria-live="polite">
          {summary}
        </p>
      )}
      {findError && <ErrorState message={findError} />}

      {list.loading && !list.data && <LoadingState label="Loading candidates..." />}
      {list.error && <ErrorState message={list.error} onRetry={() => void list.reload()} />}
      {list.data && list.data.length === 0 && (
        <EmptyState title="No candidates yet" message="Use the button to look for similar reports." />
      )}
      {list.data && list.data.length > 0 && (
        <ul className="mt-4 space-y-3">
          {list.data.map((suggestion) => (
            <li key={suggestion.id}>
              <SuggestionCard suggestion={suggestion} onChanged={() => void list.reload()} />
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
