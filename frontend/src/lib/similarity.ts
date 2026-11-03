export const THRESHOLD_OPTIONS = [0.5, 0.6, 0.7, 0.8, 0.9]
export const TOP_K_OPTIONS = [3, 5, 10]

// The backend uses the same starting values. The 0.80 has not been tested against labelled duplicates.
export const DEFAULT_THRESHOLD = 0.8
export const DEFAULT_TOP_K = 5

/** Cosine similarity with three digits. It is a score, not a probability. */
export function formatSimilarity(value: number): string {
  return value.toFixed(3)
}
