import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { AxiosError } from 'axios'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { getDashboardSummary } from '../services/dashboard'
import type { DashboardSummary } from '../types/dashboard'
import DashboardPage from './DashboardPage'

vi.mock('../services/dashboard', () => ({
  getDashboardSummary: vi.fn(),
}))

const mockedGetSummary = vi.mocked(getDashboardSummary)

// Example values for the tests (they look like a real response, but they are only test data).
const summary: DashboardSummary = {
  total_reports: 2006,
  severity_distribution: {
    blocker: 15,
    critical: 140,
    major: 118,
    normal: 1617,
    minor: 72,
    trivial: 44,
    unlabeled: 0,
  },
  predictions_total: 3,
  reports_with_predictions: 1,
  pending_reviews: 0,
  duplicate_suggestions: { pending: 2, confirmed: 0, rejected: 1 },
  duplicate_suggestions_total: 3,
}

describe('DashboardPage', () => {
  beforeEach(() => {
    mockedGetSummary.mockReset()
  })

  it('shows the cards and the number of reports for each severity', async () => {
    mockedGetSummary.mockResolvedValue(summary)
    render(<DashboardPage />)

    expect(await screen.findByText('2,006')).toBeInTheDocument()
    expect(screen.getByText('2 pending, 0 confirmed, 1 rejected')).toBeInTheDocument()

    const list = screen.getByRole('list', { name: 'Reports per severity' })
    expect(within(list).getByText('blocker')).toBeInTheDocument()
    expect(within(list).getByText('1,617')).toBeInTheDocument()
    expect(within(list).queryByText('unlabeled')).not.toBeInTheDocument()
  })

  it('shows an empty state when there are no reports', async () => {
    mockedGetSummary.mockResolvedValue({ ...summary, total_reports: 0 })
    render(<DashboardPage />)

    expect(await screen.findByText('No bug reports yet')).toBeInTheDocument()
    expect(screen.queryByRole('list', { name: 'Reports per severity' })).not.toBeInTheDocument()
  })

  it('shows an error and loads again when Try again is clicked', async () => {
    const user = userEvent.setup()
    const networkError = new AxiosError('Network Error', 'ERR_NETWORK')
    mockedGetSummary.mockRejectedValueOnce(networkError)
    mockedGetSummary.mockResolvedValueOnce(summary)
    render(<DashboardPage />)

    expect(await screen.findByRole('alert')).toHaveTextContent('Cannot reach the server')
    await user.click(screen.getByRole('button', { name: 'Try again' }))

    expect(await screen.findByText('2,006')).toBeInTheDocument()
    expect(mockedGetSummary).toHaveBeenCalledTimes(2)
  })

  it('asks the backend again when Refresh is clicked', async () => {
    const user = userEvent.setup()
    mockedGetSummary.mockResolvedValue(summary)
    render(<DashboardPage />)

    await screen.findByText('2,006')
    expect(mockedGetSummary).toHaveBeenCalledTimes(1)

    await user.click(screen.getByRole('button', { name: 'Refresh' }))
    await waitFor(() => expect(mockedGetSummary).toHaveBeenCalledTimes(2))
  })
})
