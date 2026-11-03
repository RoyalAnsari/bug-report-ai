import { useCallback, useEffect, useState } from 'react'
import { errorMessage } from '../services/api'

/**
 * Runs an async function once, and again whenever reload() is called.
 * Pass a function that does not change between renders (for example one imported from a service file).
 */
export function useAsyncData<T>(fetcher: () => Promise<T>) {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      setData(await fetcher())
    } catch (e) {
      setData(null)
      setError(errorMessage(e))
    } finally {
      setLoading(false)
    }
  }, [fetcher])

  useEffect(() => {
    void load()
  }, [load])

  return { data, error, loading, reload: load }
}
