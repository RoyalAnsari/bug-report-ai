import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { AxiosError } from 'axios'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { getModel, getModels } from '../services/models'
import type { ModelDetail, ModelSummary } from '../types/models'
import ModelsPage from './ModelsPage'

vi.mock('../services/models', () => ({
  getModels: vi.fn(),
  getModel: vi.fn(),
}))

const mockedGetModels = vi.mocked(getModels)
const mockedGetModel = vi.mocked(getModel)

// Example values for the tests (they are only test data).
const summaries: ModelSummary[] = [
  {
    id: 'duplicate-detector:v1',
    name: 'duplicate-detector',
    version: 'v1',
    task: 'duplicate candidate retrieval',
    has_evaluation: false,
    macro_f1: null,
    created_at: null,
  },
  {
    id: 'severity-classifier:v1',
    name: 'severity-classifier',
    version: 'v1',
    task: 'severity classification',
    has_evaluation: true,
    macro_f1: 0.422,
    created_at: null,
  },
]

const severity: ModelDetail = {
  id: 'severity-classifier:v1',
  name: 'severity-classifier',
  version: 'v1',
  task: 'severity classification',
  algorithm: 'TF-IDF + LinearSVC',
  variant: 'C_word_char_project_balanced',
  uses_offsets: true,
  labels: ['blocker', 'normal'],
  artifact_path: null,
  training: {
    seed: 42,
    resample_target: 5000,
    validation_macro_f1: 0.433,
    library_versions: { python: '3.14.7', scikit_learn: '1.9.1' },
  },
  evaluation: {
    split: 'test',
    macro_f1: 0.422,
    macro_precision: 0.493,
    macro_recall: 0.398,
    per_class: {
      blocker: { precision: 0.793, recall: 0.291, f1: 0.426, support: 79 },
      normal: { precision: 0.879, recall: 0.863, f1: 0.871, support: 7144 },
    },
    confusion_matrix: [
      [23, 56],
      [981, 6163],
    ],
    labels_order: ['blocker', 'normal'],
    rows: 7223,
  },
  evaluation_note: null,
  config: null,
  created_at: null,
  updated_at: null,
}

const duplicate: ModelDetail = {
  id: 'duplicate-detector:v1',
  name: 'duplicate-detector',
  version: 'v1',
  task: 'duplicate candidate retrieval',
  algorithm: 'Sentence Transformer embeddings + cosine similarity',
  variant: 'sentence-transformers/all-MiniLM-L6-v2',
  uses_offsets: null,
  labels: null,
  artifact_path: null,
  training: null,
  evaluation: null,
  evaluation_note: 'No verified duplicate pairs are available, so precision and recall were not measured.',
  config: { model: 'sentence-transformers/all-MiniLM-L6-v2', rows: 87716, default_threshold: 0.8 },
  created_at: null,
  updated_at: null,
}

describe('ModelsPage', () => {
  beforeEach(() => {
    mockedGetModels.mockReset()
    mockedGetModel.mockReset()
    mockedGetModel.mockImplementation(async (name) => (name === 'severity-classifier' ? severity : duplicate))
  })

  it('shows the saved evaluation of the model that has one', async () => {
    mockedGetModels.mockResolvedValue(summaries)
    render(<ModelsPage />)

    expect(await screen.findByText('Macro F1')).toBeInTheDocument()
    expect(screen.getByText('0.422')).toBeInTheDocument()
    expect(mockedGetModel).toHaveBeenCalledWith('severity-classifier', 'v1')

    const table = screen.getByRole('table', { name: 'Precision, recall and F1 for each severity' })
    expect(within(table).getByText('0.793')).toBeInTheDocument()
    expect(screen.getByText('6,163')).toBeInTheDocument()
    expect(screen.getByText('86%')).toBeInTheDocument()
    expect(screen.getByText('The lowest F1 is for blocker (0.426), normal (0.871).')).toBeInTheDocument()
  })

  it('says that the duplicate model was not measured and does not invent numbers', async () => {
    const user = userEvent.setup()
    mockedGetModels.mockResolvedValue(summaries)
    render(<ModelsPage />)
    await screen.findByText('Macro F1')

    await user.selectOptions(screen.getByLabelText('Model'), 'duplicate-detector:v1')

    expect(await screen.findByText('Not measured')).toBeInTheDocument()
    expect(
      screen.getByText('No verified duplicate pairs are available, so precision and recall were not measured.'),
    ).toBeInTheDocument()
    expect(screen.getByText('Default minimum similarity')).toBeInTheDocument()
    expect(screen.queryByText('Macro F1')).not.toBeInTheDocument()
  })

  it('tells how to register models when there are none', async () => {
    mockedGetModels.mockResolvedValue([])
    render(<ModelsPage />)

    expect(await screen.findByText('No models are registered')).toBeInTheDocument()
  })

  it('shows an error and loads again when Try again is clicked', async () => {
    const user = userEvent.setup()
    mockedGetModels.mockRejectedValueOnce(new AxiosError('Network Error', 'ERR_NETWORK'))
    mockedGetModels.mockResolvedValueOnce(summaries)
    render(<ModelsPage />)

    expect(await screen.findByRole('alert')).toHaveTextContent('Cannot reach the server')
    await user.click(screen.getByRole('button', { name: 'Try again' }))

    expect(await screen.findByText('Macro F1')).toBeInTheDocument()
  })

  it('shows the backend message when the evaluation cannot be loaded', async () => {
    mockedGetModels.mockResolvedValue(summaries)
    mockedGetModel.mockRejectedValue(
      new AxiosError('Request failed', 'ERR_BAD_REQUEST', undefined, undefined, {
        status: 404,
        data: { error: { code: 404, message: 'Model version not found' } },
      } as never),
    )
    render(<ModelsPage />)

    expect(await screen.findByRole('alert')).toHaveTextContent('Model version not found')
  })
})
