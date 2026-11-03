interface Props {
  headers: string[]
  rows: Record<string, string>[]
}

export default function PreviewTable({ headers, rows }: Props) {
  if (rows.length === 0) return null
  return (
    <div className="overflow-x-auto rounded-lg border border-slate-200">
      <table className="min-w-full divide-y divide-slate-200 text-sm">
        <caption className="sr-only">First rows of the file</caption>
        <thead className="bg-slate-50">
          <tr>
            {headers.map((header) => (
              <th key={header} scope="col" className="px-3 py-2 text-left font-medium text-slate-700">
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 bg-white">
          {rows.map((row, index) => (
            <tr key={index}>
              {headers.map((header) => (
                <td key={header} className="max-w-xs truncate px-3 py-2 text-slate-800" title={row[header] ?? ''}>
                  {row[header] ?? ''}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
