import { formatNumber } from '../lib/format'
import { formatScore } from '../lib/evaluation'
import type { ClassRow } from '../lib/evaluation'
import SeverityBadge from './SeverityBadge'

interface Props {
  rows: ClassRow[]
}

export default function ClassMetricsTable({ rows }: Props) {
  const head = 'px-3 py-2 text-right font-medium text-slate-700'
  return (
    <div className="overflow-x-auto rounded-lg border border-slate-200">
      <table className="min-w-full divide-y divide-slate-200 text-sm">
        <caption className="sr-only">Precision, recall and F1 for each severity</caption>
        <thead className="bg-slate-50">
          <tr>
            <th scope="col" className="px-3 py-2 text-left font-medium text-slate-700">Severity</th>
            <th scope="col" className={head}>Precision</th>
            <th scope="col" className={head}>Recall</th>
            <th scope="col" className={head}>F1</th>
            <th scope="col" className={head}>Reports</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 bg-white">
          {rows.map((row) => (
            <tr key={row.label}>
              <td className="px-3 py-2">
                <SeverityBadge label={row.label} />
              </td>
              <td className="px-3 py-2 text-right text-slate-800">{formatScore(row.precision)}</td>
              <td className="px-3 py-2 text-right text-slate-800">{formatScore(row.recall)}</td>
              <td className="px-3 py-2 text-right font-medium text-slate-900">{formatScore(row.f1)}</td>
              <td className="px-3 py-2 text-right text-slate-800">{formatNumber(row.support)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
