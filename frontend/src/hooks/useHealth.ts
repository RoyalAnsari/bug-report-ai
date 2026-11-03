import { useCallback, useEffect, useState } from 'react'
import { errorMessage, getHealth } from '../services/api'
import type { HealthResponse } from '../types/health'

export function useHealth() {
  const [data, setData] = useState<HealthResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      setData(await getHealth())
    } catch (e) {
      setData(null)
      setError(errorMessage(e))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  return { data, error, loading, reload: load }
}
