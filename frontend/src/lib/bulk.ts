export const STEP_SIZES = [100, 200, 500]
export const DEFAULT_STEP_SIZE = 200

/** Whole percent of the work that is done, never below 0 or above 100. */
export function progressPercent(done: number, target: number): number {
  if (target <= 0) return 0
  return Math.min(100, Math.max(0, Math.round((done / target) * 100)))
}
