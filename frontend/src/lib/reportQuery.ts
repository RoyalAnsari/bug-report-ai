import type { ReportQuery } from '../types/reports'
import { SEVERITY_ORDER } from './severity'

export const PAGE_SIZES = [10, 20, 50]

export const SORT_OPTIONS = [
  { value: 'newest', label: 'Newest first', sortBy: 'created_at', order: 'desc' },
  { value: 'oldest', label: 'Oldest first', sortBy: 'created_at', order: 'asc' },
  { value: 'updated', label: 'Recently updated', sortBy: 'updated_at', order: 'desc' },
  { value: 'project', label: 'Project (A to Z)', sortBy: 'project', order: 'asc' },
] as const

export const DEFAULT_QUERY: ReportQuery = {
  page: 1,
  pageSize: 20,
  search: '',
  project: '',
  severity: '',
  sort: 'newest',
}

/** The backend wants sort_by and order, the page only keeps one short name. */
export function sortParams(sort: string): { sortBy: string; order: string } {
  const option = SORT_OPTIONS.find((item) => item.value === sort) ?? SORT_OPTIONS[0]
  return { sortBy: option.sortBy, order: option.order }
}

/** Reads the page address. Anything that is not valid falls back to the default. */
export function parseQuery(params: URLSearchParams): ReportQuery {
  const page = Number(params.get('page'))
  const size = Number(params.get('size'))
  const severity = params.get('severity') ?? ''
  const sort = params.get('sort') ?? ''
  return {
    page: Number.isInteger(page) && page >= 1 ? page : DEFAULT_QUERY.page,
    pageSize: PAGE_SIZES.includes(size) ? size : DEFAULT_QUERY.pageSize,
    search: (params.get('q') ?? '').trim(),
    project: params.get('project') ?? '',
    severity: (SEVERITY_ORDER as readonly string[]).includes(severity) ? severity : '',
    sort: SORT_OPTIONS.some((item) => item.value === sort) ? sort : DEFAULT_QUERY.sort,
  }
}

/** Writes the query into the page address. Values that are the default are left out. */
export function toSearchParams(query: ReportQuery): URLSearchParams {
  const params = new URLSearchParams()
  if (query.search) params.set('q', query.search)
  if (query.project) params.set('project', query.project)
  if (query.severity) params.set('severity', query.severity)
  if (query.sort !== DEFAULT_QUERY.sort) params.set('sort', query.sort)
  if (query.pageSize !== DEFAULT_QUERY.pageSize) params.set('size', String(query.pageSize))
  if (query.page !== DEFAULT_QUERY.page) params.set('page', String(query.page))
  return params
}

export function hasActiveFilters(query: ReportQuery): boolean {
  return Boolean(query.search || query.project || query.severity)
}
