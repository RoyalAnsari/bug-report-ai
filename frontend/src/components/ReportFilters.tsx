import { useState } from 'react'
import type { FormEvent } from 'react'
import { PAGE_SIZES, SORT_OPTIONS, hasActiveFilters } from '../lib/reportQuery'
import { SEVERITY_ORDER } from '../lib/severity'
import type { ReportQuery } from '../types/reports'

interface Props {
  query: ReportQuery
  projects: string[]
  onChange: (patch: Partial<ReportQuery>) => void
  onClear: () => void
}

const selectClass =
  'mt-1 block w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500'

// This part is its own component so the text box starts again from the address whenever the search changes.
function SearchBox({ initial, onSearch }: { initial: string; onSearch: (text: string) => void }) {
  const [text, setText] = useState(initial)

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    onSearch(text.trim())
  }

  return (
    <form onSubmit={handleSubmit} className="flex items-end gap-2">
      <div className="flex-1">
        <label htmlFor="report-search" className="block text-sm font-medium text-slate-700">
          Search reports
        </label>
        <input
          id="report-search"
          type="search"
          value={text}
          maxLength={200}
          onChange={(event) => setText(event.target.value)}
          placeholder="Words from the bug text"
          className="mt-1 block w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
      </div>
      <button
        type="submit"
        className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
      >
        Search
      </button>
    </form>
  )
}

export default function ReportFilters({ query, projects, onChange, onClear }: Props) {
  // If the address names a project that is not in the list, still show it in the dropdown.
  const projectOptions = Array.from(new Set([...projects, query.project].filter(Boolean)))

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4">
      <SearchBox key={query.search} initial={query.search} onSearch={(text) => onChange({ search: text })} />

      <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div>
          <label htmlFor="filter-severity" className="block text-sm font-medium text-slate-700">Severity</label>
          <select
            id="filter-severity"
            value={query.severity}
            onChange={(event) => onChange({ severity: event.target.value })}
            className={selectClass}
          >
            <option value="">All severities</option>
            {SEVERITY_ORDER.map((label) => (
              <option key={label} value={label}>{label}</option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="filter-project" className="block text-sm font-medium text-slate-700">Project</label>
          <select
            id="filter-project"
            value={query.project}
            onChange={(event) => onChange({ project: event.target.value })}
            className={selectClass}
          >
            <option value="">All projects</option>
            {projectOptions.map((name) => (
              <option key={name} value={name}>{name}</option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="filter-sort" className="block text-sm font-medium text-slate-700">Sort by</label>
          <select
            id="filter-sort"
            value={query.sort}
            onChange={(event) => onChange({ sort: event.target.value })}
            className={selectClass}
          >
            {SORT_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>{option.label}</option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="filter-size" className="block text-sm font-medium text-slate-700">Per page</label>
          <select
            id="filter-size"
            value={query.pageSize}
            onChange={(event) => onChange({ pageSize: Number(event.target.value) })}
            className={selectClass}
          >
            {PAGE_SIZES.map((size) => (
              <option key={size} value={size}>{size}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="mt-4">
        <button
          type="button"
          onClick={onClear}
          disabled={!hasActiveFilters(query)}
          className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50"
        >
          Clear filters
        </button>
      </div>
    </div>
  )
}
