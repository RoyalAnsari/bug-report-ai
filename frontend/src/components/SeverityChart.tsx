import { Bar, BarChart, CartesianGrid, Cell, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { SEVERITY_COLORS } from '../lib/severity'
import type { SeverityRow } from '../lib/severity'

interface Props {
  data: SeverityRow[]
}

// The chart is only for looking at. The same numbers are listed as text next to it,
// so the chart is hidden from screen readers.
export default function SeverityChart({ data }: Props) {
  return (
    <div className="h-72 w-full" aria-hidden="true">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 20, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="label" />
          <YAxis allowDecimals={false} />
          <Tooltip />
          <Bar dataKey="count" name="Reports">
            {data.map((row) => (
              <Cell key={row.label} fill={SEVERITY_COLORS[row.label] ?? '#94a3b8'} />
            ))}
            <LabelList dataKey="count" position="top" />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
