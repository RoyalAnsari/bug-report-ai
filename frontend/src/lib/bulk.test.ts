import { describe, expect, it } from 'vitest'
import { DEFAULT_STEP_SIZE, STEP_SIZES, progressPercent } from './bulk'

describe('progressPercent', () => {
  it('gives the whole percent that is done', () => {
    expect(progressPercent(400, 2000)).toBe(20)
    expect(progressPercent(1, 3)).toBe(33)
  })

  it('never goes below 0 or above 100', () => {
    expect(progressPercent(-5, 100)).toBe(0)
    expect(progressPercent(250, 100)).toBe(100)
  })

  it('is 0 when there is nothing to do', () => {
    expect(progressPercent(0, 0)).toBe(0)
    expect(STEP_SIZES).toContain(DEFAULT_STEP_SIZE)
  })
})
