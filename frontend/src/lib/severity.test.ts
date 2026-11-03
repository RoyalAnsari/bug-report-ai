import { describe, expect, it } from 'vitest'
import { toChartData } from './severity'

describe('toChartData', () => {
  it('returns the six labels in a fixed order and fills missing ones with zero', () => {
    const rows = toChartData({ normal: 5, blocker: 2 })
    expect(rows.map((row) => row.label)).toEqual(['blocker', 'critical', 'major', 'normal', 'minor', 'trivial'])
    expect(rows.find((row) => row.label === 'blocker')?.count).toBe(2)
    expect(rows.find((row) => row.label === 'critical')?.count).toBe(0)
  })

  it('adds "unlabeled" only when it is not zero', () => {
    expect(toChartData({ unlabeled: 0 }).some((row) => row.label === 'unlabeled')).toBe(false)
    const rows = toChartData({ unlabeled: 3 })
    expect(rows[rows.length - 1]).toEqual({ label: 'unlabeled', count: 3 })
  })
})
