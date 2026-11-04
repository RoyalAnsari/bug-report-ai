// Token sirf is tab ke liye (sessionStorage) rakha jata hai: tab band hone par login khatam.
const KEY = 'bug_report_ai_token'

function storage(): Storage | null {
  try {
    return typeof window === 'undefined' ? null : window.sessionStorage
  } catch {
    return null
  }
}

export function getToken(): string | null {
  try {
    return storage()?.getItem(KEY) ?? null
  } catch {
    return null
  }
}

export function setToken(token: string): void {
  try {
    storage()?.setItem(KEY, token)
  } catch {
    // Storage band ho to login sirf is page load tak chalta hai.
  }
}

export function clearToken(): void {
  try {
    storage()?.removeItem(KEY)
  } catch {
    // Kuch karne ki zaroorat nahi.
  }
}
