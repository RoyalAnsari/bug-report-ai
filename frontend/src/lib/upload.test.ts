import { describe, expect, it } from 'vitest'
import { MAX_UPLOAD_BYTES, validateFile } from './upload'

describe('validateFile', () => {
  it('accepts a normal csv file, also with a capital extension', () => {
    expect(validateFile(new File(['a,b'], 'bugs.csv'))).toBeNull()
    expect(validateFile(new File(['a,b'], 'BUGS.CSV'))).toBeNull()
  })

  it('rejects files that are not csv', () => {
    expect(validateFile(new File(['a'], 'notes.txt'))).toBe('Only .csv files are accepted')
  })

  it('rejects an empty file', () => {
    expect(validateFile(new File([], 'bugs.csv'))).toBe('File is empty')
  })

  it('rejects a file that is too large', () => {
    const big = new File([new Uint8Array(MAX_UPLOAD_BYTES + 1)], 'big.csv')
    expect(validateFile(big)).toContain('too large')
  })
})
