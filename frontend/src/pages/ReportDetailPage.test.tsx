import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { AxiosError } from 'axios'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { getReportDuplicates } from '../services/duplicates'
import { getPredictionReview, predictReport, submitReview } from '../services/predictions'
import { getReport, getReportPredictions } from '../services/reports'
import { getSettings } from '../services/settings'
import type { PredictionRecord } from '../types/prediction'
import type { ReportItem } from '../types/reports'
import type { ReviewRecord } from '../types/review'
import ReportDetailPage from './ReportDetailPage'

vi.mock('../services/reports', () => ({
  getReport: vi.fn(),
  getReportPredictions: vi.fn(),
}))

vi.mock('../services/predictions', () => ({
  predictReport: vi.fn(),
  getPredictionReview: vi.fn(),
  submitReview: vi.fn(),
}))

vi.mock('../services/duplicates', () => ({
  findDuplicates: vi.fn(),
  getReportDuplicates: vi.fn(),
  reviewSuggestion: vi.fn(),
}))

vi.mock('../services/settings', () => ({
  getSettings: vi.fn(),
}))

const mockedGetReport = vi.mocked(getReport)
const mockedGetPredictions = vi.mocked(getReportPredictions)
const mockedPredict = vi.mocked(predictReport)
const mockedGetReview = vi.mocked(getPredictionReview)
const mockedSubmit = vi.mocked(submitReview)
const mockedGetDuplicates = vi.mocked(getReportDuplicates)
const mockedGetSettings = vi.mocked(getSettings)

// Example values for the tests (they are only test data).
const report: ReportItem = {
  id: 'br_1',
  text: 'Crash on save',
  project: 'Core',
  severity: 'major',
  external_id: '77',
  source: 'csv:bugs.csv',
  created_at: '2026-10-30T12:00:00Z',
  updated_at: '2026-10-30T12:05:00Z',
}

const prediction: PredictionRecord = {
  id: 'pred_1',
  report_id: 'br_1',
  label: 'trivial',
  margin: 0.0893,
  needs_review: true,
  scores: { trivial: 0.1143, normal: 0.025 },
  model_version: 'tfidf-linearsvc-v1',
  created_at: '2026-10-31T06:26:12Z',
  note: 'margin is a score gap, not a probability',
}

const review: ReviewRecord = {
  id: 'fb_pred_1',
  prediction_id: 'pred_1',
  report_id: 'br_1',
  action: 'confirm',
  predicted_label: 'trivial',
  final_label: 'trivial',
  note: null,
  created_at: '2026-10-31T07:00:00Z',
}

function renderDetail(id = 'br_1') {
  return render(
    <MemoryRouter initialEntries={[`/reports/${id}`]}>
      <Routes>
        <Route path="/reports/:reportId" element={<ReportDetailPage />} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('ReportDetailPage', () => {
  beforeEach(() => {
    mockedGetReport.mockReset()
    mockedGetPredictions.mockReset()
    mockedPredict.mockReset()
    mockedGetReview.mockReset()
    mockedSubmit.mockReset()
    mockedGetDuplicates.mockReset()
    mockedGetSettings.mockReset()
    mockedGetReport.mockResolvedValue(report)
    mockedGetReview.mockResolvedValue(null)
    mockedGetDuplicates.mockResolvedValue([])
    mockedGetSettings.mockResolvedValue({
      values: { review_margin: 0.25, duplicate_threshold: 0.8, duplicate_top_k: 5 },
      defaults: { review_margin: 0.25, duplicate_threshold: 0.8, duplicate_top_k: 5 },
      application: { api_version: 'v1', cors_origins: [], database: 'bug_report_ai', models_loaded: { severity: true, duplicates: true } },
      updated_at: null,
    })
  })

  it('shows the report and its predictions', async () => {
    mockedGetPredictions.mockResolvedValue([prediction])
    renderDetail()

    expect(await screen.findByText('Crash on save')).toBeInTheDocument()
    expect(screen.getByText('Core')).toBeInTheDocument()
    expect(await screen.findByText('Margin: 0.0893')).toBeInTheDocument()
    expect(screen.getByText('Needs review')).toBeInTheDocument()
    expect(screen.getByText('Model: tfidf-linearsvc-v1')).toBeInTheDocument()
    expect(mockedGetReport).toHaveBeenCalledWith('br_1')
  })

  it('shows the possible duplicates section for the report', async () => {
    mockedGetPredictions.mockResolvedValue([])
    renderDetail()

    expect(await screen.findByRole('button', { name: 'Find possible duplicates' })).toBeInTheDocument()
     await waitFor(() => expect(mockedGetDuplicates).toHaveBeenCalledWith('br_1'))
  })

  it('says when there are no predictions yet', async () => {
    mockedGetPredictions.mockResolvedValue([])
    renderDetail()

    expect(await screen.findByText('No predictions yet')).toBeInTheDocument()
    expect(screen.queryByText('Review the latest prediction')).not.toBeInTheDocument()
  })

  it('shows the message from the backend when the report does not exist', async () => {
    const notFound = new AxiosError('Request failed', 'ERR_BAD_REQUEST', undefined, undefined, {
      status: 404,
      data: { error: { code: 404, message: 'Report not found' } },
    } as never)
    mockedGetReport.mockRejectedValue(notFound)
    mockedGetPredictions.mockResolvedValue([])
    renderDetail('br_missing')

    expect(await screen.findByRole('alert')).toHaveTextContent('Report not found')
    expect(screen.getByRole('link', { name: 'Back to reports' })).toHaveAttribute('href', '/reports')
  })

  it('predicts the report and shows the new prediction', async () => {
    const user = userEvent.setup()
    mockedGetPredictions.mockResolvedValueOnce([])
    mockedGetPredictions.mockResolvedValueOnce([prediction])
    mockedPredict.mockResolvedValue(prediction)
    renderDetail()
    await screen.findByText('No predictions yet')

    await user.click(screen.getByRole('button', { name: 'Predict severity' }))

    expect(await screen.findByText('Margin: 0.0893')).toBeInTheDocument()
    expect(mockedPredict).toHaveBeenCalledWith('br_1')
  })

  it('shows the backend message when the model is not loaded', async () => {
    const user = userEvent.setup()
    mockedGetPredictions.mockResolvedValue([])
    mockedPredict.mockRejectedValue(
      new AxiosError('Request failed', 'ERR_BAD_RESPONSE', undefined, undefined, {
        status: 503,
        data: { error: { code: 503, message: 'Severity model is not loaded' } },
      } as never),
    )
    renderDetail()
    await screen.findByText('No predictions yet')

    await user.click(screen.getByRole('button', { name: 'Predict severity' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Severity model is not loaded')
  })

  it('confirms the latest prediction and loads the report again', async () => {
    const user = userEvent.setup()
    mockedGetPredictions.mockResolvedValue([prediction])
    mockedSubmit.mockResolvedValue(review)
    renderDetail()

    await user.click(await screen.findByRole('button', { name: 'Confirm prediction' }))

    expect(await screen.findByText('Prediction confirmed')).toBeInTheDocument()
    expect(mockedSubmit).toHaveBeenCalledWith('pred_1', { action: 'confirm' })
    await waitFor(() => expect(mockedGetReport).toHaveBeenCalledTimes(2))
  })

  it('corrects the prediction only after a severity is chosen', async () => {
    const user = userEvent.setup()
    mockedGetPredictions.mockResolvedValue([prediction])
    mockedSubmit.mockResolvedValue({ ...review, action: 'correct', final_label: 'major' })
    renderDetail()

    const saveButton = await screen.findByRole('button', { name: 'Save correction' })
    expect(saveButton).toBeDisabled()

    await user.selectOptions(screen.getByLabelText('Or choose the right severity'), 'major')
    expect(saveButton).toBeEnabled()
    await user.click(saveButton)

    expect(await screen.findByText('Prediction corrected')).toBeInTheDocument()
    expect(mockedSubmit).toHaveBeenCalledWith('pred_1', { action: 'correct', label: 'major' })
  })

  it('shows the review instead of the form when the prediction was reviewed already', async () => {
    mockedGetPredictions.mockResolvedValue([prediction])
    mockedGetReview.mockResolvedValue({ ...review, action: 'correct', final_label: 'major' })
    renderDetail()

    expect(await screen.findByText('Prediction corrected')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Confirm prediction' })).not.toBeInTheDocument()
  })
})
