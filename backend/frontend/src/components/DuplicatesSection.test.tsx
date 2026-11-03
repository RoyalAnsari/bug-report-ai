import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { AxiosError } from 'axios'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { findDuplicates, getReportDuplicates, reviewSuggestion } from '../services/duplicates'
import { getSettings } from '../services/settings'
import type { Suggestion } from '../types/duplicates'
import type { SettingsResponse } from '../types/settings'
import DuplicatesSection from './DuplicatesSection'

vi.mock('../services/duplicates', () => ({
  findDuplicates: vi.fn(),
  getReportDuplicates: vi.fn(),
  reviewSuggestion: vi.fn(),
}))

vi.mock('../services/settings', () => ({
  getSettings: vi.fn(),
}))

const mockedFind = vi.mocked(findDuplicates)
const mockedList = vi.mocked(getReportDuplicates)
const mockedReview = vi.mocked(reviewSuggestion)
const mockedSettings = vi.mocked(getSettings)

// Example values for the tests (they are only test data).
const pending: Suggestion = {
  id: 'dup_1',
  report_id: 'br_1',
  candidate_id: '200',
  candidate_text: 'Crash when saving',
  candidate_project: 'Core',
  similarity: 0.873,
  score_type: 'cosine similarity (not a probability)',
  status: 'pending',
  created_at: null,
}

const defaultSettings: SettingsResponse = {
  values: { review_margin: 0.25, duplicate_threshold: 0.8, duplicate_top_k: 5 },
  defaults: { review_margin: 0.25, duplicate_threshold: 0.8, duplicate_top_k: 5 },
  application: {
    api_version: 'v1',
    cors_origins: [],
    database: 'bug_report_ai',
    models_loaded: { severity: true, duplicates: true },
  },
  updated_at: null,
}

describe('DuplicatesSection', () => {
  beforeEach(() => {
    mockedFind.mockReset()
    mockedList.mockReset()
    mockedReview.mockReset()
    mockedSettings.mockReset()
    mockedSettings.mockResolvedValue(defaultSettings)
  })

  it('shows the candidates that exist, with similarity and status', async () => {
    mockedList.mockResolvedValue([pending])
    render(<DuplicatesSection reportId="br_1" />)

    expect(await screen.findByText('Crash when saving')).toBeInTheDocument()
    expect(screen.getByText('Similarity: 0.873')).toBeInTheDocument()
    expect(screen.getByText('Pending')).toBeInTheDocument()
    expect(mockedList).toHaveBeenCalledWith('br_1')
  })

  it('searches with the chosen settings and shows the new candidates', async () => {
    const user = userEvent.setup()
    mockedList.mockResolvedValueOnce([])
    mockedList.mockResolvedValueOnce([pending])
    mockedFind.mockResolvedValue({ report_id: 'br_1', threshold: 0.7, found: 1, new: 1, suggestions: [pending] })
    render(<DuplicatesSection reportId="br_1" />)
    await screen.findByText('No candidates yet')

    await user.selectOptions(screen.getByLabelText('Minimum similarity'), '0.7')
    await user.click(screen.getByRole('button', { name: 'Find possible duplicates' }))

    expect(await screen.findByText('Found 1 possible duplicate, 1 new.')).toBeInTheDocument()
    expect(await screen.findByText('Crash when saving')).toBeInTheDocument()
    expect(mockedFind).toHaveBeenCalledWith('br_1', { top_k: 5, threshold: 0.7 })
  })

  it('starts from the values saved on the Settings page', async () => {
    const user = userEvent.setup()
    mockedSettings.mockResolvedValue({
      ...defaultSettings,
      values: { review_margin: 0.25, duplicate_threshold: 0.75, duplicate_top_k: 10 },
    })
    mockedList.mockResolvedValue([])
    mockedFind.mockResolvedValue({ report_id: 'br_1', threshold: 0.75, found: 0, new: 0, suggestions: [] })
    render(<DuplicatesSection reportId="br_1" />)
    await screen.findByText('No candidates yet')

    await waitFor(() => expect(screen.getByLabelText('Minimum similarity')).toHaveValue('0.75'))
    await user.click(screen.getByRole('button', { name: 'Find possible duplicates' }))

    expect(mockedFind).toHaveBeenCalledWith('br_1', { top_k: 10, threshold: 0.75 })
  })

  it('suggests a lower similarity when nothing was found', async () => {
    const user = userEvent.setup()
    mockedList.mockResolvedValue([])
    mockedFind.mockResolvedValue({ report_id: 'br_1', threshold: 0.8, found: 0, new: 0, suggestions: [] })
    render(<DuplicatesSection reportId="br_1" />)
    await screen.findByText('No candidates yet')

    await user.click(screen.getByRole('button', { name: 'Find possible duplicates' }))

    expect(
      await screen.findByText('No candidates reached a similarity of 0.80. Try a lower minimum similarity.'),
    ).toBeInTheDocument()
  })

  it('shows the backend message when the model is not loaded', async () => {
    const user = userEvent.setup()
    mockedList.mockResolvedValue([])
    mockedFind.mockRejectedValue(
      new AxiosError('Request failed', 'ERR_BAD_RESPONSE', undefined, undefined, {
        status: 503,
        data: { error: { code: 503, message: 'Duplicate model is not loaded' } },
      } as never),
    )
    render(<DuplicatesSection reportId="br_1" />)
    await screen.findByText('No candidates yet')

    await user.click(screen.getByRole('button', { name: 'Find possible duplicates' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Duplicate model is not loaded')
  })

  it('confirms a candidate and shows its new status', async () => {
    const user = userEvent.setup()
    mockedList.mockResolvedValueOnce([pending])
    mockedList.mockResolvedValueOnce([{ ...pending, status: 'confirmed' }])
    mockedReview.mockResolvedValue({ ...pending, status: 'confirmed' })
    render(<DuplicatesSection reportId="br_1" />)

    await user.click(await screen.findByRole('button', { name: 'Confirm duplicate' }))

    expect(await screen.findByText('Confirmed duplicate')).toBeInTheDocument()
    expect(mockedReview).toHaveBeenCalledWith('dup_1', 'confirm')
    expect(screen.queryByRole('button', { name: 'Confirm duplicate' })).not.toBeInTheDocument()
  })
})
