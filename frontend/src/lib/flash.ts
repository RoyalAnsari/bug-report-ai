// Ek chhota paigham jo agle page (jaise login page) par dikhana ho, sirf is tab ke liye.
const KEY = 'bug_report_ai_flash'

function storage(): Storage | null {
  try {
    return typeof window === 'undefined' ? null : window.sessionStorage
  } catch {
    return null
  }
}

export function setFlash(message: string): void {
  try {
    storage()?.setItem(KEY, message)
  } catch {
    // Paigham na dikhe to koi nuqsan nahi.
  }
}

export function peekFlash(): string | null {
  try {
    return storage()?.getItem(KEY) ?? null
  } catch {
    return null
  }
}

export function clearFlash(): void {
  try {
    storage()?.removeItem(KEY)
  } catch {
    // Kuch karne ki zaroorat nahi.
  }
}
