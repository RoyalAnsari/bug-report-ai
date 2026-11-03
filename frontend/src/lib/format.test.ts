import { describe, expect, it } from 'vitest'
import { formatNumber } from './format'

describe('formatNumber', () => {
  it('adds thousands separators', () => {
    expect(formatNumber(2006)).toBe('2,006')
    expect(formatNumber(0)).toBe('0')
  })
})
