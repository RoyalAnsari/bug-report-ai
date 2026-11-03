import { describe, expect, it } from 'vitest'
import { parseQueueQuery, toQueueParams } from './duplicateQueue'

describe('parseQueueQuery', () => {
  it('shows pending suggestions on page 1 by default', () => {
    expect(parseQueueQuery(new URLSearchParams(''))).toEqual({ status: 'pending', page: 1, pageSize: 20 })
  })

  it('ignores values that are not valid', () => {
    expect(parseQueueQuery(new URLSearchParams('status=weird&page=0'))).toEqual({
      status: 'pending',
      page: 1,
      pageSize: 20,
    })
  })

  it('can be read back after toQueueParams', () => {
    const query = { status: 'rejected' as const, page: 3, pageSize: 20 }
    expect(parseQueueQuery(toQueueParams(query))).toEqual(query)
    expect(toQueueParams({ status: 'pending', page: 1, pageSize: 20 }).toString()).toBe('')
  })
})
