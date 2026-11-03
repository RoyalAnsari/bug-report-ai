import { describe, expect, it } from 'vitest'
import { toForm, validateForm } from './settings'

const values = { review_margin: 0.25, duplicate_threshold: 0.8, duplicate_top_k: 5 }

describe('toForm', () => {
  it('turns the numbers into text for the boxes', () => {
    expect(toForm(values)).toEqual({ review_margin: '0.25', duplicate_threshold: '0.8', duplicate_top_k: '5' })
  })
})

describe('validateForm', () => {
  it('gives the numbers when everything is fine', () => {
    expect(validateForm(toForm(values))).toEqual({ values, errors: {} })
  })

  it('asks for a number when a box is empty or not a number', () => {
    const result = validateForm({ review_margin: '', duplicate_threshold: 'abc', duplicate_top_k: '5' })
    expect(result.values).toBeNull()
    expect(result.errors).toEqual({ review_margin: 'Enter a number', duplicate_threshold: 'Enter a number' })
  })

  it('shows the limits when a number is too small or too big', () => {
    const result = validateForm({ review_margin: '9', duplicate_threshold: '-0.1', duplicate_top_k: '51' })
    expect(result.errors).toEqual({
      review_margin: 'Must be between 0 and 5',
      duplicate_threshold: 'Must be between 0 and 1',
      duplicate_top_k: 'Must be between 1 and 50',
    })
  })

  it('wants a whole number of candidates', () => {
    const result = validateForm({ ...toForm(values), duplicate_top_k: '2.5' })
    expect(result.errors).toEqual({ duplicate_top_k: 'Must be a whole number' })
  })
})
