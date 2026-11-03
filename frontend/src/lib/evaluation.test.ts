import { describe, expect, it } from 'vitest'
import type { Evaluation } from '../types/models'
import { cellColor, formatScore, rowShare, toClassRows, weakestClasses } from './evaluation'

// Example values for the tests (they are only test data).
const evaluation: Evaluation = {
  split: 'test',
  macro_f1: 0.5,
  macro_precision: 0.5,
  macro_recall: 0.5,
  per_class: {
    blocker: { precision: 0.8, recall: 0.3, f1: 0.43, support: 79 },
    normal: { precision: 0.88, recall: 0.86, f1: 0.87, support: 7144 },
    minor: { precision: 0.14, recall: 0.17, f1: 0.15, support: 310 },
  },
  confusion_matrix: [
    [23, 56],
    [981, 6163],
  ],
  labels_order: ['blocker', 'normal', 'minor'],
  rows: 7533,
}

describe('toClassRows', () => {
  it('keeps the order of the confusion matrix and uses zero for a missing class', () => {
    const rows = toClassRows(evaluation)
    expect(rows.map((row) => row.label)).toEqual(['blocker', 'normal', 'minor'])
    expect(rows[1]).toEqual({ label: 'normal', precision: 0.88, recall: 0.86, f1: 0.87, support: 7144 })
    const missing = toClassRows({ ...evaluation, labels_order: ['trivial'] })
    expect(missing[0]).toEqual({ label: 'trivial', precision: 0, recall: 0, f1: 0, support: 0 })
  })
})

describe('weakestClasses', () => {
  it('lists the lowest F1 first', () => {
    const weakest = weakestClasses(toClassRows(evaluation), 2)
    expect(weakest.map((row) => row.label)).toEqual(['minor', 'blocker'])
  })
})

describe('rowShare', () => {
  it('is the part of a real class that went into a predicted class', () => {
    expect(rowShare(evaluation.confusion_matrix, 0, 0)).toBeCloseTo(23 / 79)
    expect(rowShare(evaluation.confusion_matrix, 1, 1)).toBeCloseTo(6163 / 7144)
  })

  it('is zero when a class has no rows', () => {
    expect(rowShare([[0, 0]], 0, 1)).toBe(0)
  })
})

describe('cellColor and formatScore', () => {
  it('makes a bigger share darker', () => {
    const alpha = (color: string) => Number(color.replace(/.*, ([\d.]+)\)$/, '$1'))
    expect(alpha(cellColor(0.9))).toBeGreaterThan(alpha(cellColor(0.1)))
    expect(alpha(cellColor(5))).toBe(alpha(cellColor(1)))
  })

  it('shows three digits, or a dash when there is no value', () => {
    expect(formatScore(0.42203)).toBe('0.422')
    expect(formatScore(null)).toBe('-')
  })
})
