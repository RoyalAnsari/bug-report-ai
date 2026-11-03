import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { ClassRow } from '../lib/evaluation'

interface Props {
  rows: ClassRow[]
}

// The chart is only for looking at. The same numbers are in the table next to it,
// so the chart is hidden from screen readers.
export default function ClassMetricsChart({ rows }: Props) {
  return (
    <div className="h-72 w-full" aria-hidden="true">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={rows} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="label" />
          <YAxis domain={[0, 1]} />
          <Tooltip />
          <Legend />
          <Bar dataKey="precision" name="Precision" fill="#4f46e5" />
          <Bar dataKey="recall" name="Recall" fill="#0ea5e9" />
          <Bar dataKey="f1" name="F1" fill="#10b981" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
