import { formatNumber } from '../lib/format'

interface Props {
  page: number
  pages: number
  pageSize: number
  total: number
  onPageChange: (page: number) => void
  disabled?: boolean
  /** What is being counted, for the text "Showing 1 to 20 of 45 reports". */
  noun?: string
}

const buttonClass =
  'rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50'

export default function Pagination({
  page,
  pages,
  pageSize,
  total,
  onPageChange,
  disabled = false,
  noun = 'reports',
}: Props) {
  const first = total === 0 ? 0 : (page - 1) * pageSize + 1
  const last = Math.min(page * pageSize, total)

  return (
    <nav aria-label="Pagination" className="mt-4 flex flex-wrap items-center justify-between gap-3">
      <p className="text-sm text-slate-600" aria-live="polite">
        {`Showing ${formatNumber(first)} to ${formatNumber(last)} of ${formatNumber(total)} ${noun}`}
      </p>
      <div className="flex items-center gap-2">
        <button
          type="button"
          aria-label="Previous page"
          disabled={disabled || page <= 1}
          onClick={() => onPageChange(page - 1)}
          className={buttonClass}
        >
          Previous
        </button>
        <span className="text-sm text-slate-700">{`Page ${formatNumber(page)} of ${formatNumber(Math.max(pages, 1))}`}</span>
        <button
          type="button"
          aria-label="Next page"
          disabled={disabled || page >= pages}
          onClick={() => onPageChange(page + 1)}
          className={buttonClass}
        >
          Next
        </button>
      </div>
    </nav>
  )
}
