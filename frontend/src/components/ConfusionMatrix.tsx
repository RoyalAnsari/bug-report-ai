import { cellColor, rowShare } from '../lib/evaluation'
import { formatNumber } from '../lib/format'

interface Props {
  labels: string[]
  matrix: number[][]
}

export default function ConfusionMatrix({ labels, matrix }: Props) {
  return (
    <div className="overflow-x-auto">
      <table className="border-separate border-spacing-1 text-sm">
        <caption className="mb-2 text-left text-sm text-slate-600">
          Each row is the real severity, each column is the predicted severity. The colour shows the share of the row,
          and the diagonal is what the model got right.
        </caption>
        <thead>
          <tr>
            <th scope="col" className="p-2 text-left text-xs font-medium text-slate-500">
              Real \ Predicted
            </th>
            {labels.map((label) => (
              <th key={label} scope="col" className="p-2 text-xs font-medium text-slate-700">
                {label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {matrix.map((row, i) => (
            <tr key={labels[i]}>
              <th scope="row" className="p-2 text-left text-xs font-medium text-slate-700">
                {labels[i]}
              </th>
              {row.map((count, j) => {
                const share = rowShare(matrix, i, j)
                const tone = share > 0.5 ? 'text-white' : 'text-slate-900'
                const diagonal = i === j ? 'font-semibold ring-1 ring-indigo-600' : ''
                return (
                  <td
                    key={labels[j]}
                    style={{ backgroundColor: cellColor(share) }}
                    className={`min-w-16 rounded p-2 text-center ${tone} ${diagonal}`}
                    title={`${labels[i]} predicted as ${labels[j]}: ${count}`}
                  >
                    <div>{formatNumber(count)}</div>
                    <div className="text-xs opacity-80">{`${Math.round(share * 100)}%`}</div>
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
