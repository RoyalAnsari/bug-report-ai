import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { AxiosError } from 'axios'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { getProjects, getReports } from '../services/reports'
import type { ReportItem, ReportListResponse } from '../types/reports'
import ReportsPage from './ReportsPage'

vi.mock('../services/reports', () => ({
  getReports: vi.fn(),
  getProjects: vi.fn(),
}))

const mockedGetReports = vi.mocked(getReports)
const mockedGetProjects = vi.mocked(getProjects)

function item(id: string, text: string, severity: string | null): ReportItem {
  return {
    id,
    text,
    project: 'Core',
    severity,
    external_id: '1',
    source: 'test',
    created_at: '2026-10-30T12:00:00Z',
    updated_at: '2026-10-30T12:00:00Z',
  }
}

// Example values for the tests (they are only test data).
const listResponse: ReportListResponse = {
  items: [item('br_1', 'Crash on save', 'major'), item('br_2', 'Typo in menu', null)],
  total: 45,
  page: 1,
  page_size: 20,
  pages: 3,
}

function renderPage(entry = '/reports') {
  return render(
    <MemoryRouter initialEntries={[entry]}>
      <ReportsPage />
    </MemoryRouter>,
  )
}

function lastQuery() {
  const calls = mockedGetReports.mock.calls
  return calls[calls.length - 1][0]
}

describe('ReportsPage', () => {
  beforeEach(() => {
    mockedGetReports.mockReset()
    mockedGetProjects.mockReset()
    mockedGetProjects.mockResolvedValue(['Core', 'JDT'])
  })

  it('shows the reports, the total and the projects', async () => {
    mockedGetReports.mockResolvedValue(listResponse)
    renderPage()

    expect(await screen.findByText('Crash on save')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Crash on save' })).toHaveAttribute('href', '/reports/br_1')
    expect(screen.getByText('Not labeled')).toBeInTheDocument()
    expect(screen.getByText('Showing 1 to 20 of 45 reports')).toBeInTheDocument()
    expect(await screen.findByRole('option', { name: 'JDT' })).toBeInTheDocument()
  })

  it('asks for the chosen severity and goes back to page 1', async () => {
    const user = userEvent.setup()
    mockedGetReports.mockResolvedValue(listResponse)
    renderPage()
    await screen.findByText('Crash on save')

    await user.selectOptions(screen.getByLabelText('Severity'), 'major')

    await waitFor(() => expect(lastQuery()).toMatchObject({ severity: 'major', page: 1 }))
  })

  it('searches when the Search button is clicked', async () => {
    const user = userEvent.setup()
    mockedGetReports.mockResolvedValue(listResponse)
    renderPage()
    await screen.findByText('Crash on save')

    await user.type(screen.getByLabelText('Search reports'), 'crash')
    await user.click(screen.getByRole('button', { name: 'Search' }))

    await waitFor(() => expect(lastQuery()).toMatchObject({ search: 'crash', page: 1 }))
  })

  it('moves to the next page', async () => {
    const user = userEvent.setup()
    mockedGetReports.mockResolvedValue(listResponse)
    renderPage()
    await screen.findByText('Crash on save')

    expect(screen.getByRole('button', { name: 'Previous page' })).toBeDisabled()
    await user.click(screen.getByRole('button', { name: 'Next page' }))

    await waitFor(() => expect(lastQuery()).toMatchObject({ page: 2 }))
  })

  it('shows an empty state and clears the filters', async () => {
    const user = userEvent.setup()
    mockedGetReports.mockResolvedValue({ items: [], total: 0, page: 1, page_size: 20, pages: 0 })
    renderPage('/reports?severity=major')

    expect(await screen.findByText('No reports match your filters')).toBeInTheDocument()
    expect(lastQuery()).toMatchObject({ severity: 'major' })

    await user.click(screen.getByRole('button', { name: 'Clear filters' }))

    await waitFor(() => expect(lastQuery()).toMatchObject({ severity: '' }))
  })

  it('shows an error and loads again when Try again is clicked', async () => {
    const user = userEvent.setup()
    mockedGetReports.mockRejectedValueOnce(new AxiosError('Network Error', 'ERR_NETWORK'))
    mockedGetReports.mockResolvedValueOnce(listResponse)
    renderPage()

    expect(await screen.findByRole('alert')).toHaveTextContent('Cannot reach the server')
    await user.click(screen.getByRole('button', { name: 'Try again' }))

    expect(await screen.findByText('Crash on save')).toBeInTheDocument()
  })
})
