import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { evaluateCsv } from '../services/triage'
import type { EvaluationResult } from '../types/triage'
import EvaluatePage from './EvaluatePage'

vi.mock('../services/triage', () => ({
  triageReport: vi.fn(),
  evaluateCsv: vi.fn(),
}))

const labels = ['blocker', 'critical', 'major', 'normal', 'minor', 'trivial']

const result: EvaluationResult = {
  model_version: 'distilbert-base-uncased-v2',
  rows_used: 3,
  rows_skipped: 1,
  skipped_examples: ['row 5: empty text'],
  accuracy: 0.6667,
  macro_f1: 0.389,
  majority_baseline_accuracy: 0.6667,
  labels,
  per_class: labels.map((label) => ({ label, precision: 0.5, recall: 0.5, f1: 0.5, support: label === 'normal' ? 2 : 0 })),
  confusion_matrix: labels.map((_, row) => labels.map((__, column) => (row === column ? 1 : 0))),
  warnings: ['Only 3 usable rows. With fewer than 200 the numbers are rough.'],
}

describe('EvaluatePage', () => {
  beforeEach(() => {
    vi.resetAllMocks()
  })

  it('needs a file before it can evaluate', () => {
    render(<EvaluatePage />)
    expect(screen.getByRole('button', { name: 'Evaluate' })).toBeDisabled()
  })

  it('sends the chosen file and shows accuracy, F1, warnings and the confusion matrix', async () => {
    vi.mocked(evaluateCsv).mockResolvedValue(result)
    const user = userEvent.setup()
    render(<EvaluatePage />)

    const file = new File(['text,severity\nCrash,normal\n'], 'labelled.csv', { type: 'text/csv' })
    await user.upload(screen.getByLabelText('CSV file'), file)
    await user.click(screen.getByRole('button', { name: 'Evaluate' }))

    expect(evaluateCsv).toHaveBeenCalledWith(file)
    expect(await screen.findByTestId('accuracy')).toHaveTextContent('66.7%')
    expect(screen.getByTestId('macro-f1')).toHaveTextContent('0.389')
    expect(screen.getByTestId('rows-used')).toHaveTextContent('3')
    expect(screen.getByText(/Only 3 usable rows/)).toBeInTheDocument()
    expect(screen.getByText('row 5: empty text')).toBeInTheDocument()
    expect(screen.getByText(/Confusion matrix/)).toBeInTheDocument()
  })

  it('shows the server message when the file is not usable', async () => {
    vi.mocked(evaluateCsv).mockRejectedValue(new Error('bad file'))
    const user = userEvent.setup()
    render(<EvaluatePage />)
    await user.upload(screen.getByLabelText('CSV file'), new File(['x'], 'x.csv', { type: 'text/csv' }))
    await user.click(screen.getByRole('button', { name: 'Evaluate' }))
    expect(await screen.findByRole('alert')).toBeInTheDocument()
  })
})
