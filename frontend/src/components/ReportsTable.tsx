import { Link } from 'react-router-dom'
import { formatDateTime } from '../lib/format'
import type { ReportItem } from '../types/reports'
import SeverityBadge from './SeverityBadge'

interface Props {
  reports: ReportItem[]
}

export default function ReportsTable({ reports }: Props) {
  return (
    <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
      <table className="min-w-full divide-y divide-slate-200 text-sm">
        <caption className="sr-only">Bug reports</caption>
        <thead className="bg-slate-50">
          <tr>
            <th scope="col" className="px-3 py-2 text-left font-medium text-slate-700">Bug text</th>
            <th scope="col" className="px-3 py-2 text-left font-medium text-slate-700">Project</th>
            <th scope="col" className="px-3 py-2 text-left font-medium text-slate-700">Severity</th>
            <th scope="col" className="px-3 py-2 text-left font-medium text-slate-700">Bug ID</th>
            <th scope="col" className="px-3 py-2 text-left font-medium text-slate-700">Added</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {reports.map((report) => (
            <tr key={report.id}>
              <td className="max-w-md px-3 py-2">
                <Link
                  to={`/reports/${report.id}`}
                  className="block truncate font-medium text-indigo-700 hover:underline"
                  title={report.text}
                >
                  {report.text}
                </Link>
              </td>
              <td className="px-3 py-2 text-slate-700">{report.project ?? '-'}</td>
              <td className="px-3 py-2">
                {report.severity ? (
                  <SeverityBadge label={report.severity} />
                ) : (
                  <span className="text-xs text-slate-500">Not labeled</span>
                )}
              </td>
              <td className="px-3 py-2 text-slate-700">{report.external_id ?? '-'}</td>
              <td className="whitespace-nowrap px-3 py-2 text-slate-700">{formatDateTime(report.created_at)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
