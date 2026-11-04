import { useState } from 'react'
import type { FormEvent } from 'react'
import { useAuth } from '../auth/useAuth'
import { errorMessage } from '../services/api'
import { changePassword } from '../services/auth'

const MIN_PASSWORD = 12

export default function AccountPage() {
  const auth = useAuth()
  const [current, setCurrent] = useState('')
  const [next, setNext] = useState('')
  const [confirm, setConfirm] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [done, setDone] = useState(false)

  if (!auth.authEnabled || !auth.user) {
    return <p className="text-sm text-slate-600">Login is switched off on this server, so there is no account to manage.</p>
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setDone(false)
    if (next.length < MIN_PASSWORD) {
      setError(`The new password must be at least ${MIN_PASSWORD} characters long.`)
      return
    }
    if (next !== confirm) {
      setError('The new passwords do not match.')
      return
    }
    if (next === current) {
      setError('The new password must be different from the current one.')
      return
    }
    setError(null)
    setSaving(true)
    try {
      await changePassword(current, next)
      setCurrent('')
      setNext('')
      setConfirm('')
      setDone(true)
    } catch (problem) {
      setError(errorMessage(problem))
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="max-w-md space-y-6">
      <div>
        <h1 className="text-xl font-semibold">My account</h1>
        <p className="mt-1 text-sm text-slate-600">
          {auth.user.name} ({auth.user.email}), role: {auth.user.role}
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4 rounded-lg border border-slate-200 bg-white p-4">
        <h2 className="text-base font-semibold">Change password</h2>

        {error && (
          <p role="alert" className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">
            {error}
          </p>
        )}
        {done && (
          <p role="status" className="rounded-md border border-green-200 bg-green-50 px-3 py-2 text-sm text-green-800">
            Password changed.
          </p>
        )}

        <div>
          <label htmlFor="current-password" className="mb-1 block text-sm font-medium text-slate-700">
            Current password
          </label>
          <input
            id="current-password"
            type="password"
            autoComplete="current-password"
            required
            maxLength={128}
            value={current}
            onChange={(event) => setCurrent(event.target.value)}
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
          />
        </div>

        <div>
          <label htmlFor="new-password" className="mb-1 block text-sm font-medium text-slate-700">
            New password
          </label>
          <input
            id="new-password"
            type="password"
            autoComplete="new-password"
            required
            maxLength={128}
            value={next}
            onChange={(event) => setNext(event.target.value)}
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
          />
          <p className="mt-1 text-xs text-slate-500">At least {MIN_PASSWORD} characters.</p>
        </div>

        <div>
          <label htmlFor="confirm-password" className="mb-1 block text-sm font-medium text-slate-700">
            Confirm new password
          </label>
          <input
            id="confirm-password"
            type="password"
            autoComplete="new-password"
            required
            maxLength={128}
            value={confirm}
            onChange={(event) => setConfirm(event.target.value)}
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
          />
        </div>

        <button
          type="submit"
          disabled={saving}
          className="rounded-md bg-indigo-600 px-3 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-60"
        >
          {saving ? 'Saving...' : 'Change password'}
        </button>
      </form>
    </div>
  )
}
