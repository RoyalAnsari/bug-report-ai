import { beforeEach, describe, expect, it } from 'vitest'
import { clearToken, getToken, setToken } from './authStorage'

describe('authStorage', () => {
  beforeEach(() => {
    window.sessionStorage.clear()
  })

  it('returns null when nothing is stored', () => {
    expect(getToken()).toBeNull()
  })

  it('stores and reads the token', () => {
    setToken('abc')
    expect(getToken()).toBe('abc')
  })

  it('clears the token', () => {
    setToken('abc')
    clearToken()
    expect(getToken()).toBeNull()
  })
})
