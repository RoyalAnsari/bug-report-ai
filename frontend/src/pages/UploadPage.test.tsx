import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { importUpload, previewUpload } from '../services/upload'
import type { ImportResult, UploadPreview } from '../types/upload'
import UploadPage from './UploadPage'

vi.mock('../services/upload', () => ({
  previewUpload: vi.fn(),
  importUpload: vi.fn(),
}))

const mockedPreview = vi.mocked(previewUpload)
const mockedImport = vi.mocked(importUpload)

// Example values for the tests (they are only test data).
const goodPreview: UploadPreview = {
  filename: 'bugs.csv',
  encoding: 'utf-8',
  headers: ['Issue ID', 'Summary', 'Severity', 'Product'],
  mapping: { text: 'Summary', severity: 'Severity', project: 'Product', external_id: 'Issue ID' },
  needs_mapping: false,
  preview: [{ 'Issue ID': '1', Summary: 'Crash on save', Severity: 'major', Product: 'Core' }],
  total_rows: 3,
  valid_rows: 2,
  error_count: 1,
  errors: [{ row: 3, message: 'Text is shorter than 3 characters' }],
  errors_truncated: false,
}

const importResult: ImportResult = {
  total_rows: 3,
  valid_rows: 2,
  error_count: 1,
  errors: [{ row: 3, message: 'Text is shorter than 3 characters' }],
  errors_truncated: false,
  inserted: 1,
  already_existed: 1,
  merged_duplicates: 0,
}

function renderPage() {
  return render(
    <MemoryRouter>
      <UploadPage />
    </MemoryRouter>,
  )
}

function csvFile(name = 'bugs.csv') {
  return new File(['Summary\nCrash on save\n'], name, { type: 'text/csv' })
}

describe('UploadPage', () => {
  beforeEach(() => {
    mockedPreview.mockReset()
    mockedImport.mockReset()
  })

  it('shows a preview and imports the file after Import is clicked', async () => {
    const user = userEvent.setup()
    mockedPreview.mockResolvedValue(goodPreview)
    mockedImport.mockResolvedValue(importResult)
    renderPage()

    const file = csvFile()
    await user.upload(screen.getByLabelText('CSV file'), file)

    expect(await screen.findByText('Crash on save')).toBeInTheDocument()
    expect(screen.getByText('Row 3')).toBeInTheDocument()
    expect(mockedPreview).toHaveBeenCalledWith(file, null)

    await user.click(screen.getByRole('button', { name: 'Import 2 valid rows' }))

    expect(await screen.findByText('Import finished')).toBeInTheDocument()
    expect(mockedImport).toHaveBeenCalledWith(file, goodPreview.mapping)
    expect(screen.getByText('New reports added')).toBeInTheDocument()
  })

  it('rejects a file that is not csv without calling the backend', async () => {
    const user = userEvent.setup({ applyAccept: false })
    renderPage()

    await user.upload(screen.getByLabelText('CSV file'), csvFile('notes.txt'))

    expect(await screen.findByRole('alert')).toHaveTextContent('Only .csv files are accepted')
    expect(mockedPreview).not.toHaveBeenCalled()
  })

  it('asks for a text column and sends the new mapping when one is chosen', async () => {
    const user = userEvent.setup()
    const unknownColumns: UploadPreview = {
      ...goodPreview,
      headers: ['A', 'B'],
      mapping: { text: null, severity: null, project: null, external_id: null },
      needs_mapping: true,
      preview: [{ A: 'some crash text', B: 'major' }],
      valid_rows: 0,
      error_count: 0,
      errors: [],
    }
    const afterChoosing: UploadPreview = {
      ...unknownColumns,
      mapping: { text: 'A', severity: null, project: null, external_id: null },
      needs_mapping: false,
      valid_rows: 1,
    }
    mockedPreview.mockResolvedValueOnce(unknownColumns)
    mockedPreview.mockResolvedValueOnce(afterChoosing)
    renderPage()

    await user.upload(screen.getByLabelText('CSV file'), csvFile())
    expect(await screen.findByText('Choose which column holds the bug text.')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /^Import/ })).toBeDisabled()

    await user.selectOptions(screen.getByLabelText('Bug text (required)'), 'A')

    await waitFor(() => expect(mockedPreview).toHaveBeenCalledTimes(2))
    expect(mockedPreview.mock.calls[1][1]).toEqual({
      text: 'A',
      severity: null,
      project: null,
      external_id: null,
    })
    expect(await screen.findByRole('button', { name: 'Import 1 valid row' })).toBeEnabled()
  })

  it('accepts a file dropped on the drop area', async () => {
    mockedPreview.mockResolvedValue(goodPreview)
    renderPage()

    fireEvent.drop(screen.getByTestId('dropzone'), { dataTransfer: { files: [csvFile()] } })

    expect(await screen.findByText('Crash on save')).toBeInTheDocument()
    expect(mockedPreview).toHaveBeenCalledTimes(1)
  })
})
