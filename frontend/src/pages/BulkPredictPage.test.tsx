import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { AxiosError } from 'axios'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { getBulkStatus, runBulkPredict } from '../services/bulk'
import type { BulkResult, BulkStatus } from '../types/bulk'
import BulkPredictPage from './BulkPredictPage'

vi.mock('../services/bulk', () => ({
  getBulkStatus: vi.fn(),
  runBulkPredict: vi.fn(),
}))

const mockedStatus = vi.mocked(getBulkStatus)
const mockedRun = vi.mocked(runBulkPredict)

// Example values for the tests (they are only test data).
const before: BulkStatus = { total_reports: 2006, reports_with_predictions: 1, unpredicted: 2005 }
const after: BulkStatus = { total_reports: 2006, reports_with_predictions: 2006, unpredicted: 0 }

function result(predicted: number, needsReview: number, remaining: number): BulkResult {
  return {
    requested: predicted,
    predicted,
    needs_review: needsReview,
    remaining,
    model_version: 'tfidf-linearsvc-v1',
    note: 'margin is a score gap, not a probability',
  }
}

function renderPage() {
  return render(
    <MemoryRouter>
      <BulkPredictPage />
    </MemoryRouter>,
  )
}

describe('BulkPredictPage', () => {
  beforeEach(() => {
    mockedStatus.mockReset()
    mockedRun.mockReset()
  })

  it('shows how many reports have a prediction and how many do not', async () => {
    mockedStatus.mockResolvedValue(before)
    renderPage()

    expect(await screen.findByText('2,005')).toBeInTheDocument()
    expect(screen.getByText('2,006')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Predict all unpredicted reports' })).toBeEnabled()
  })

  it('predicts step by step until nothing is left and shows the summary', async () => {
    const user = userEvent.setup()
    mockedStatus.mockResolvedValueOnce(before)
    mockedStatus.mockResolvedValueOnce(after)
    mockedRun.mockResolvedValueOnce(result(10, 4, 5))
    mockedRun.mockResolvedValueOnce(result(5, 2, 0))
    renderPage()

    await user.click(await screen.findByRole('button', { name: 'Predict all unpredicted reports' }))

    expect(
      await screen.findByText('Predicted 15 reports. 6 of them need review. 0 reports are still without a prediction.'),
    ).toBeInTheDocument()
    expect(mockedRun).toHaveBeenCalledTimes(2)
    expect(mockedRun).toHaveBeenCalledWith(200)
    expect(await screen.findByText('Every report already has a prediction.')).toBeInTheDocument()
  })

  it('stops after the current step when Stop is clicked', async () => {
    const user = userEvent.setup()
    mockedStatus.mockResolvedValue(before)
    let finishFirstStep: (value: BulkResult) => void = () => {}
    mockedRun.mockImplementationOnce(
      () =>
        new Promise<BulkResult>((resolve) => {
          finishFirstStep = resolve
        }),
    )
    renderPage()

    await user.click(await screen.findByRole('button', { name: 'Predict all unpredicted reports' }))
    await user.click(await screen.findByRole('button', { name: 'Stop' }))
    finishFirstStep(result(10, 4, 5))

    expect(await screen.findByText(/Stopped after the current batch/)).toBeInTheDocument()
    expect(mockedRun).toHaveBeenCalledTimes(1)
  })

  it('shows the backend message when the model is not loaded', async () => {
    const user = userEvent.setup()
    mockedStatus.mockResolvedValue(before)
    mockedRun.mockRejectedValue(
      new AxiosError('Request failed', 'ERR_BAD_RESPONSE', undefined, undefined, {
        status: 503,
        data: { error: { code: 503, message: 'Severity model is not loaded' } },
      } as never),
    )
    renderPage()

    await user.click(await screen.findByRole('button', { name: 'Predict all unpredicted reports' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Severity model is not loaded')
  })

  it('does not offer to predict when every report already has a prediction', async () => {
    mockedStatus.mockResolvedValue(after)
    renderPage()

    expect(await screen.findByText('Every report already has a prediction.')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Predict all unpredicted reports' })).toBeDisabled()
  })
})
