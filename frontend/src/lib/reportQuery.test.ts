import { describe, expect, it } from 'vitest'
import { DEFAULT_QUERY, hasActiveFilters, parseQuery, sortParams, toSearchParams } from './reportQuery'

describe('parseQuery', () => {
  it('uses the defaults when the address has nothing', () => {
    expect(parseQuery(new URLSearchParams(''))).toEqual(DEFAULT_QUERY)
  })

  it('ignores values that are not valid', () => {
    const params = new URLSearchParams('page=-3&size=7&severity=urgent&sort=weird')
    expect(parseQuery(params)).toEqual(DEFAULT_QUERY)
  })

  it('reads valid values', () => {
    const params = new URLSearchParams('q=crash&project=Core&severity=major&sort=oldest&size=50&page=3')
    expect(parseQuery(params)).toEqual({
      page: 3,
      pageSize: 50,
      search: 'crash',
      project: 'Core',
      severity: 'major',
      sort: 'oldest',
    })
  })
})

describe('toSearchParams', () => {
  it('leaves default values out of the address', () => {
    expect(toSearchParams(DEFAULT_QUERY).toString()).toBe('')
  })

  it('can be read back with parseQuery', () => {
    const query = { page: 2, pageSize: 10, search: 'login crash', project: 'Core', severity: 'minor', sort: 'project' }
    expect(parseQuery(toSearchParams(query))).toEqual(query)
  })
})

describe('other helpers', () => {
  it('turns the sort name into the values the backend wants', () => {
    expect(sortParams('oldest')).toEqual({ sortBy: 'created_at', order: 'asc' })
    expect(sortParams('unknown')).toEqual({ sortBy: 'created_at', order: 'desc' })
  })

  it('knows when a filter is used', () => {
    expect(hasActiveFilters(DEFAULT_QUERY)).toBe(false)
    expect(hasActiveFilters({ ...DEFAULT_QUERY, severity: 'major' })).toBe(true)
  })
})
