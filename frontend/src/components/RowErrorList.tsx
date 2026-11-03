import { formatNumber } from '../lib/format'
import type { RowError } from '../types/upload'

interface Props {
  errors: RowError[]
  total: number
  truncated: boolean
}

export default function RowErrorList({ errors, total, truncated }: Props) {
  if (total === 0) return null
  return (
    <div className="mt-4 rounded-lg border border-amber-200 bg-amber-50 p-4 text-amber-900">
      <h3 className="font-medium">{`${formatNumber(total)} rows have problems and will be skipped`}</h3>
      <p className="mt-1 text-xs">Row numbers count the data rows. The header line is not counted.</p>
      <ul className="mt-2 max-h-48 space-y-1 overflow-y-auto text-sm">
        {errors.map((error) => (
          <li key={error.row}>
            <span className="font-medium">{`Row ${error.row}`}</span>
            {`: ${error.message}`}
          </li>
        ))}
      </ul>
      {truncated && <p className="mt-2 text-xs">{`Only the first ${errors.length} problems are shown.`}</p>}
    </div>
  )
}
