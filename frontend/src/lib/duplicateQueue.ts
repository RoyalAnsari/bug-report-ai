export type QueueStatus = 'pending' | 'confirmed' | 'rejected' | 'all'

export const QUEUE_STATUSES: { value: QueueStatus; label: string }[] = [
  { value: 'pending', label: 'Pending' },
  { value: 'confirmed', label: 'Confirmed' },
  { value: 'rejected', label: 'Rejected' },
  { value: 'all', label: 'All' },
]

export const QUEUE_PAGE_SIZE = 20

export interface QueueQuery {
  status: QueueStatus
  page: number
  pageSize: number
}

/** Reads the page address. Anything that is not valid falls back to the default. */
export function parseQueueQuery(params: URLSearchParams): QueueQuery {
  const status = params.get('status')
  const page = Number(params.get('page'))
  return {
    status: QUEUE_STATUSES.some((item) => item.value === status) ? (status as QueueStatus) : 'pending',
    page: Number.isInteger(page) && page >= 1 ? page : 1,
    pageSize: QUEUE_PAGE_SIZE,
  }
}

/** Writes the query into the page address. Default values are left out. */
export function toQueueParams(query: QueueQuery): URLSearchParams {
  const params = new URLSearchParams()
  if (query.status !== 'pending') params.set('status', query.status)
  if (query.page !== 1) params.set('page', String(query.page))
  return params
}
