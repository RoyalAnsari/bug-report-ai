import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { getSuggestions, reviewSuggestion } from '../services/duplicates'
import type { QueueItem, QueueResponse } from '../types/duplicates'
import DuplicatesPage from './DuplicatesPage'

vi.mock('../services/duplicates', () => ({
  getSuggestions: vi.fn(),
  reviewSuggestion: vi.fn(),
}))

const mockedGetSuggestions = vi.mocked(getSuggestions)
const mockedReview = vi.mocked(reviewSuggestion)

// Example values for the tests (they are only test data).
const item: QueueItem = {
  id: 'dup_1',
  report_id: 'br_1',
  candidate_id: '200',
  candidate_text: 'Crash when saving',
  candidate_project: 'Core',
  similarity: 0.873,
  score_type: 'cosine similarity (not a probability)',
  status: 'pending',
  created_at: null,
  report_text: 'Crash on save',
  report_project: 'Core',
}

const response: QueueResponse = { items: [item], total: 45, page: 1, page_size: 20, pages: 3 }

function renderPage(entry = '/duplicates') {
  return render(
    <MemoryRouter initialEntries={[entry]}>
      <DuplicatesPage />
    </MemoryRouter>,
  )
}

function lastQuery() {
  const calls = mockedGetSuggestions.mock.calls
  return calls[calls.length - 1][0]
}

describe('DuplicatesPage', () => {
  beforeEach(() => {
    mockedGetSuggestions.mockReset()
    mockedReview.mockReset()
  })

  it('shows pending suggestions with the report, the candidate and the similarity', async () => {
    mockedGetSuggestions.mockResolvedValue(response)
    renderPage()

    expect(await screen.findByText('Crash on save')).toBeInTheDocument()
    expect(screen.getByText('Crash when saving')).toBeInTheDocument()
    expect(screen.getByText('Similarity: 0.873')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Open report' })).toHaveAttribute('href', '/reports/br_1')
    expect(screen.getByText('Showing 1 to 20 of 45 suggestions')).toBeInTheDocument()
    expect(lastQuery()).toEqual({ status: 'pending', page: 1, pageSize: 20 })
  })

  it('asks for the chosen status and goes back to page 1', async () => {
    const user = userEvent.setup()
    mockedGetSuggestions.mockResolvedValue(response)
    renderPage('/duplicates?page=2')
    await screen.findByText('Crash on save')

    await user.selectOptions(screen.getByLabelText('Status'), 'rejected')

    await waitFor(() => expect(lastQuery()).toMatchObject({ status: 'rejected', page: 1 }))
  })

  it('rejects a suggestion and loads the list again', async () => {
    const user = userEvent.setup()
    mockedGetSuggestions.mockResolvedValue(response)
    mockedReview.mockResolvedValue({ ...item, status: 'rejected' })
    renderPage()

    await user.click(await screen.findByRole('button', { name: 'Reject' }))

    await waitFor(() => expect(mockedGetSuggestions).toHaveBeenCalledTimes(2))
    expect(mockedReview).toHaveBeenCalledWith('dup_1', 'reject')
  })

  it('moves to the next page', async () => {
    const user = userEvent.setup()
    mockedGetSuggestions.mockResolvedValue(response)
    renderPage()
    await screen.findByText('Crash on save')

    await user.click(screen.getByRole('button', { name: 'Next page' }))

    await waitFor(() => expect(lastQuery()).toMatchObject({ page: 2 }))
  })

  it('shows an empty state when there is nothing to review', async () => {
    mockedGetSuggestions.mockResolvedValue({ items: [], total: 0, page: 1, page_size: 20, pages: 0 })
    renderPage()

    expect(await screen.findByText('No suggestions to review')).toBeInTheDocument()
  })
})
