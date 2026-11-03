import axios from 'axios'
import type { HealthResponse } from '../types/health'

const baseURL: string = import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000/api/v1'

export const docsUrl = baseURL.replace(/\/api\/v1\/?$/, '') + '/docs'

export const api = axios.create({ baseURL, timeout: 15000 })

export function errorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const apiMessage = error.response?.data?.error?.message
    if (apiMessage) return String(apiMessage)
    if (error.code === 'ERR_NETWORK') {
      return 'Cannot reach the server. Is the backend running?'
    }
    return error.message
  }
  return 'Something went wrong'
}

export async function getHealth(): Promise<HealthResponse> {
  const { data } = await api.get<HealthResponse>('/health')
  return data
}
