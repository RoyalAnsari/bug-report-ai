import axios from 'axios'
import { clearToken, getToken } from '../lib/authStorage'
import type { HealthResponse } from '../types/health'

const baseURL: string = import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000/api/v1'

export const docsUrl = baseURL.replace(/\/api\/v1\/?$/, '') + '/docs'

export const AUTH_EXPIRED_EVENT = 'auth:expired'

export const api = axios.create({ baseURL, timeout: 15000 })

// Har request ke saath login token bhejta hai (agar maujood ho).
api.interceptors.request.use((config) => {
  const token = getToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Server 401 de (token expire ya ghalat) to token hata kar app ko batata hai ke dobara login karna hai.
api.interceptors.response.use(
  (response) => response,
  (error: unknown) => {
    if (axios.isAxiosError(error) && error.response?.status === 401 && error.config?.url !== '/auth/login') {
      clearToken()
      if (typeof window !== 'undefined') {
        window.dispatchEvent(new Event(AUTH_EXPIRED_EVENT))
      }
    }
    return Promise.reject(error)
  },
)

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
