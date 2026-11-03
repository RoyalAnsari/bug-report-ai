import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { AxiosError } from 'axios'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { getSettings, resetSettings, saveSettings } from '../services/settings'
import type { SettingsResponse } from '../types/settings'
import SettingsPage from './SettingsPage'

vi.mock('../services/settings', () => ({
  getSettings: vi.fn(),
  saveSettings: vi.fn(),
  resetSettings: vi.fn(),
}))

const mockedGet = vi.mocked(getSettings)
const mockedSave = vi.mocked(saveSettings)
const mockedReset = vi.mocked(resetSettings)

// Example values for the tests (they are only test data).
const initial: SettingsResponse = {
  values: { review_margin: 0.25, duplicate_threshold: 0.8, duplicate_top_k: 5 },
  defaults: { review_margin: 0.25, duplicate_threshold: 0.8, duplicate_top_k: 5 },
  application: {
    api_version: 'v1',
    cors_origins: ['http://localhost:5173'],
    database: 'bug_report_ai',
    models_loaded: { severity: true, duplicates: false },
  },
  updated_at: null,
}

describe('SettingsPage', () => {
  beforeEach(() => {
    mockedGet.mockReset()
    mockedSave.mockReset()
    mockedReset.mockReset()
  })

  it('shows the saved values and what the backend was started with', async () => {
    mockedGet.mockResolvedValue(initial)
    render(<SettingsPage />)

    expect(await screen.findByLabelText('Review margin')).toHaveValue(0.25)
    expect(screen.getByLabelText('Minimum similarity for duplicates')).toHaveValue(0.8)
    expect(screen.getByLabelText('Candidates to show for duplicates')).toHaveValue(5)
    expect(screen.getByText('bug_report_ai')).toBeInTheDocument()
    expect(screen.getByText('http://localhost:5173')).toBeInTheDocument()
    expect(screen.getByText('Severity model: loaded')).toBeInTheDocument()
    expect(screen.getByText('Duplicate model: not loaded')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Save settings' })).toBeDisabled()
  })

  it('saves a changed value and loads the settings again', async () => {
    const user = userEvent.setup()
    const updated = { ...initial, values: { ...initial.values, review_margin: 0.5 } }
    mockedGet.mockResolvedValueOnce(initial)
    mockedGet.mockResolvedValueOnce(updated)
    mockedSave.mockResolvedValue(updated)
    render(<SettingsPage />)

    const input = await screen.findByLabelText('Review margin')
    await user.clear(input)
    await user.type(input, '0.5')
    await user.click(screen.getByRole('button', { name: 'Save settings' }))

    expect(await screen.findByText('Settings saved.')).toBeInTheDocument()
    expect(mockedSave).toHaveBeenCalledWith({ review_margin: 0.5, duplicate_threshold: 0.8, duplicate_top_k: 5 })
    expect(mockedGet).toHaveBeenCalledTimes(2)
    expect(screen.getByLabelText('Review margin')).toHaveValue(0.5)
  })

  it('shows the limit and does not allow saving a value that is too big', async () => {
    const user = userEvent.setup()
    mockedGet.mockResolvedValue(initial)
    render(<SettingsPage />)

    const input = await screen.findByLabelText('Review margin')
    await user.clear(input)
    await user.type(input, '9')

    expect(screen.getByText('Must be between 0 and 5')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Save settings' })).toBeDisabled()
    expect(mockedSave).not.toHaveBeenCalled()
  })

  it('goes back to the saved value when Undo changes is clicked', async () => {
    const user = userEvent.setup()
    mockedGet.mockResolvedValue(initial)
    render(<SettingsPage />)

    const input = await screen.findByLabelText('Review margin')
    await user.clear(input)
    await user.type(input, '1')
    await user.click(screen.getByRole('button', { name: 'Undo changes' }))

    expect(screen.getByLabelText('Review margin')).toHaveValue(0.25)
  })

  it('resets to the defaults', async () => {
    const user = userEvent.setup()
    mockedGet.mockResolvedValue(initial)
    mockedReset.mockResolvedValue(initial)
    render(<SettingsPage />)
    await screen.findByLabelText('Review margin')

    await user.click(screen.getByRole('button', { name: 'Reset to defaults' }))

    expect(await screen.findByText('Settings were reset to the defaults.')).toBeInTheDocument()
    expect(mockedReset).toHaveBeenCalledTimes(1)
  })

  it('shows the backend message when saving does not work', async () => {
    const user = userEvent.setup()
    mockedGet.mockResolvedValue(initial)
    mockedSave.mockRejectedValue(
      new AxiosError('Request failed', 'ERR_BAD_RESPONSE', undefined, undefined, {
        status: 503,
        data: { error: { code: 503, message: 'Database is not configured' } },
      } as never),
    )
    render(<SettingsPage />)

    const input = await screen.findByLabelText('Review margin')
    await user.clear(input)
    await user.type(input, '0.5')
    await user.click(screen.getByRole('button', { name: 'Save settings' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Database is not configured')
  })

  it('shows an error and loads again when Try again is clicked', async () => {
    const user = userEvent.setup()
    mockedGet.mockRejectedValueOnce(new AxiosError('Network Error', 'ERR_NETWORK'))
    mockedGet.mockResolvedValueOnce(initial)
    render(<SettingsPage />)

    expect(await screen.findByRole('alert')).toHaveTextContent('Cannot reach the server')
    await user.click(screen.getByRole('button', { name: 'Try again' }))

    expect(await screen.findByLabelText('Review margin')).toBeInTheDocument()
  })
})
