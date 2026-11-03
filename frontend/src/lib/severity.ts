export const SEVERITY_ORDER = ['blocker', 'critical', 'major', 'normal', 'minor', 'trivial'] as const

export const SEVERITY_COLORS: Record<string, string> = {
  blocker: '#b91c1c',
  critical: '#ea580c',
  major: '#d97706',
  normal: '#0284c7',
  minor: '#64748b',
  trivial: '#a1a1aa',
  unlabeled: '#cbd5e1',
}

export interface SeverityRow {
  label: string
  count: number
}

/** Turns the API's severity counts into rows in a fixed order. "unlabeled" is added only when it is not zero. */
export function toChartData(distribution: Record<string, number>): SeverityRow[] {
  const rows: SeverityRow[] = SEVERITY_ORDER.map((label) => ({
    label,
    count: distribution[label] ?? 0,
  }))
  const unlabeled = distribution['unlabeled'] ?? 0
  if (unlabeled > 0) rows.push({ label: 'unlabeled', count: unlabeled })
  return rows
}
