import type { SettingsValues } from '../types/settings'

export type FieldName = keyof SettingsValues
export type FormValues = Record<FieldName, string>
export type FormErrors = Partial<Record<FieldName, string>>

export const FIELDS: FieldName[] = ['review_margin', 'duplicate_threshold', 'duplicate_top_k']

// The same limits as the backend. The backend checks them again.
export const LIMITS: Record<FieldName, { min: number; max: number; step: number; whole: boolean }> = {
  review_margin: { min: 0, max: 5, step: 0.05, whole: false },
  duplicate_threshold: { min: 0, max: 1, step: 0.01, whole: false },
  duplicate_top_k: { min: 1, max: 50, step: 1, whole: true },
}

export function toForm(values: SettingsValues): FormValues {
  return {
    review_margin: String(values.review_margin),
    duplicate_threshold: String(values.duplicate_threshold),
    duplicate_top_k: String(values.duplicate_top_k),
  }
}

/** Checks the text of the three boxes. Gives the numbers when all are fine, or a message for each wrong box. */
export function validateForm(form: FormValues): { values: SettingsValues | null; errors: FormErrors } {
  const errors: FormErrors = {}
  const numbers: Partial<Record<FieldName, number>> = {}

  for (const field of FIELDS) {
    const text = form[field].trim()
    const limit = LIMITS[field]
    const number = Number(text)
    if (text === '' || Number.isNaN(number)) {
      errors[field] = 'Enter a number'
    } else if (number < limit.min || number > limit.max) {
      errors[field] = `Must be between ${limit.min} and ${limit.max}`
    } else if (limit.whole && !Number.isInteger(number)) {
      errors[field] = 'Must be a whole number'
    } else {
      numbers[field] = number
    }
  }

  if (Object.keys(errors).length > 0) return { values: null, errors }
  return {
    values: {
      review_margin: numbers.review_margin as number,
      duplicate_threshold: numbers.duplicate_threshold as number,
      duplicate_top_k: numbers.duplicate_top_k as number,
    },
    errors,
  }
}
