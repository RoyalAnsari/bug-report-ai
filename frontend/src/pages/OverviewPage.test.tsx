import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { getHealth } from '../services/api'
import OverviewPage from './OverviewPage'

vi.mock('../services/api', () => ({
  getHealth: vi.fn(),
  errorMessage: (error: unknown) => (error instanceof Error ? error.message : 'Something went wrong'),
}))

const mockedGetHealth = vi.mocked(getHealth)

describe('OverviewPage', () => {
  beforeEach(() => {
    mockedGetHealth.mockReset()
  })

  it('shows the status badges returned by the backend', async () => {
    mockedGetHealth.mockResolvedValue({
      status: 'ok',
      models: { severity_loaded: true, duplicates_loaded: false },
    })
    render(<OverviewPage />)

    expect(screen.getByRole('status')).toHaveTextContent('Checking backend...')
    expect(await screen.findByText('API: ok')).toBeInTheDocument()
    expect(screen.getByText('Severity model: loaded')).toBeInTheDocument()
    expect(screen.getByText('Duplicate model: not loaded')).toBeInTheDocument()
  })

  it('shows an error and loads again when Try again is clicked', async () => {
    const user = userEvent.setup()
    mockedGetHealth.mockRejectedValueOnce(new Error('Cannot reach the server. Is the backend running?'))
    mockedGetHealth.mockResolvedValueOnce({
      status: 'ok',
      models: { severity_loaded: true, duplicates_loaded: true },
    })
    render(<OverviewPage />)

    expect(await screen.findByRole('alert')).toHaveTextContent('Cannot reach the server')
    await user.click(screen.getByRole('button', { name: 'Try again' }))

    expect(await screen.findByText('API: ok')).toBeInTheDocument()
    expect(mockedGetHealth).toHaveBeenCalledTimes(2)
  })
})
