import { describe, expect, it } from 'vitest'
import { DEFAULT_THRESHOLD, DEFAULT_TOP_K, THRESHOLD_OPTIONS, TOP_K_OPTIONS, formatSimilarity } from './similarity'

describe('formatSimilarity', () => {
  it('shows three digits', () => {
    expect(formatSimilarity(0.87349)).toBe('0.873')
    expect(formatSimilarity(1)).toBe('1.000')
  })
})

describe('defaults', () => {
  it('are part of the choices the page offers', () => {
    expect(THRESHOLD_OPTIONS).toContain(DEFAULT_THRESHOLD)
    expect(TOP_K_OPTIONS).toContain(DEFAULT_TOP_K)
  })
})
