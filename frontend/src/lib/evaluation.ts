import type { Evaluation } from '../types/models'

export interface ClassRow {
  label: string
  precision: number
  recall: number
  f1: number
  support: number
}

/** The saved per-class numbers as a list, in the same order as the confusion matrix. */
export function toClassRows(evaluation: Evaluation): ClassRow[] {
  return evaluation.labels_order.map((label) => {
    const row = evaluation.per_class[label]
    return {
      label,
      precision: row?.precision ?? 0,
      recall: row?.recall ?? 0,
      f1: row?.f1 ?? 0,
      support: row?.support ?? 0,
    }
  })
}

/** The classes with the lowest F1, weakest first. */
export function weakestClasses(rows: ClassRow[], count = 3): ClassRow[] {
  return [...rows].sort((a, b) => a.f1 - b.f1).slice(0, count)
}

/** Share of one real class that ended up in one predicted class (0 to 1). */
export function rowShare(matrix: number[][], row: number, column: number): number {
  const total = (matrix[row] ?? []).reduce((sum, value) => sum + value, 0)
  return total === 0 ? 0 : (matrix[row]?.[column] ?? 0) / total
}

/** Darker colour for a bigger share. */
export function cellColor(share: number): string {
  const clamped = Math.min(Math.max(share, 0), 1)
  const alpha = 0.06 + 0.84 * clamped
  return `rgba(79, 70, 229, ${alpha.toFixed(2)})`
}

export function formatScore(value: number | null | undefined): string {
  return value === null || value === undefined ? '-' : value.toFixed(3)
}
