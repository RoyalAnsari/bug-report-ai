import { AxiosError } from 'axios'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { api } from './api'
import { getPredictionReview } from './predictions'

vi.mock('./api', () => ({
  api: { get: vi.fn(), post: vi.fn() },
}))

const mockedGet = vi.mocked(api.get)

function errorWithStatus(status: number) {
  return new AxiosError('Request failed', 'ERR_BAD_REQUEST', undefined, undefined, { status } as never)
}

describe('getPredictionReview', () => {
  beforeEach(() => {
    mockedGet.mockReset()
  })

  it('returns null when the prediction has not been reviewed yet (404)', async () => {
    mockedGet.mockRejectedValue(errorWithStatus(404))
    await expect(getPredictionReview('pred_1')).resolves.toBeNull()
  })

  it('passes other errors on', async () => {
    mockedGet.mockRejectedValue(errorWithStatus(500))
    await expect(getPredictionReview('pred_1')).rejects.toBeInstanceOf(AxiosError)
  })
})
