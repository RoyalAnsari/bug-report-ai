import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { triageReport } from '../services/triage'
import type { TriageResult } from '../types/triage'
import TryItPage from './TryItPage'

vi.mock('../services/triage', () => ({
  triageReport: vi.fn(),
  evaluateCsv: vi.fn(),
}))

const result: TriageResult = {
  severity: { label: 'major', margin: 0.42, needs_review: true, scores: { major: 1.2, normal: 0.3 } },
  similar: [
    { bug_id: 11, project: 'Core', text: 'Crash on save', similarity: 0.91, likely_duplicate: true },
    { bug_id: 12, project: 'JDT', text: 'Another crash', similarity: 0.62, likely_duplicate: false },
  ],
  model_version: 'distilbert-base-uncased-v2',
  duplicate_threshold: 0.8,
}

describe('TryItPage', () => {
  beforeEach(() => {
    vi.resetAllMocks()
  })

  it('does not let you analyse a title that is too short', async () => {
    const user = userEvent.setup()
    render(<TryItPage />)
    expect(screen.getByRole('button', { name: 'Analyse' })).toBeDisabled()
    await user.type(screen.getByLabelText('Bug report title'), 'ab')
    expect(screen.getByRole('button', { name: 'Analyse' })).toBeDisabled()
  })

  it('shows the severity, the review notice and similar bugs', async () => {
    vi.mocked(triageReport).mockResolvedValue(result)
    const user = userEvent.setup()
    render(<TryItPage />)

    await user.type(screen.getByLabelText('Bug report title'), '  Crash on save  ')
    await user.type(screen.getByLabelText('Project (optional)'), 'Core')
    await user.click(screen.getByRole('button', { name: 'Analyse' }))

    expect(triageReport).toHaveBeenCalledWith({ text: 'Crash on save', project: 'Core' })
    expect(await screen.findByTestId('severity-label')).toHaveTextContent('major')
    expect(screen.getByText('Confidence gap: 0.42')).toBeInTheDocument()
    expect(screen.getByRole('status')).toHaveTextContent('Needs review')
    expect(screen.getByText('91% similar')).toBeInTheDocument()
    expect(screen.getByText('Likely duplicate')).toBeInTheDocument()
    expect(screen.getByText(/distilbert-base-uncased-v2/)).toBeInTheDocument()
  })

  it('sends no project when the field is empty', async () => {
    vi.mocked(triageReport).mockResolvedValue({ ...result, similar: [] })
    const user = userEvent.setup()
    render(<TryItPage />)
    await user.type(screen.getByLabelText('Bug report title'), 'Crash on save')
    await user.click(screen.getByRole('button', { name: 'Analyse' }))
    expect(triageReport).toHaveBeenCalledWith({ text: 'Crash on save', project: null })
    expect(await screen.findByText(/No similar earlier bug was found/)).toBeInTheDocument()
  })

  it('fills the box from an example', async () => {
    const user = userEvent.setup()
    render(<TryItPage />)
    await user.click(screen.getByRole('button', { name: 'Typo in the preferences dialog' }))
    expect(screen.getByLabelText('Bug report title')).toHaveValue('Typo in the preferences dialog')
    expect(screen.getByRole('button', { name: 'Analyse' })).toBeEnabled()
  })

  it('shows an error when the request fails', async () => {
    vi.mocked(triageReport).mockRejectedValue(new Error('boom'))
    const user = userEvent.setup()
    render(<TryItPage />)
    await user.type(screen.getByLabelText('Bug report title'), 'Crash on save')
    await user.click(screen.getByRole('button', { name: 'Analyse' }))
    expect(await screen.findByRole('alert')).toBeInTheDocument()
  })
})
