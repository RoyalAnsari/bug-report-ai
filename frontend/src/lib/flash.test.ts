import { beforeEach, describe, expect, it } from 'vitest'
import { clearFlash, peekFlash, setFlash } from './flash'

describe('flash', () => {
  beforeEach(() => {
    window.sessionStorage.clear()
  })

  it('returns null when nothing is stored', () => {
    expect(peekFlash()).toBeNull()
  })

  it('keeps the message until it is cleared', () => {
    setFlash('Hello')
    expect(peekFlash()).toBe('Hello')
    expect(peekFlash()).toBe('Hello')
    clearFlash()
    expect(peekFlash()).toBeNull()
  })
})
