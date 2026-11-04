import { useCallback, useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { useAuth } from '../auth/useAuth'
import { errorMessage } from '../services/api'
import { createUser, listUsers, resetUserPassword, updateUser } from '../services/users'
import type { Role } from '../types/auth'
import type { ManagedUser } from '../types/users'

const MIN_PASSWORD = 12

function formatDate(value: string | null): string {
  if (!value) return 'Never'
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? 'Never' : date.toLocaleString()
}

export default function UsersPage() {
  const auth = useAuth()
  const [users, setUsers] = useState<ManagedUser[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [email, setEmail] = useState('')
  const [name, setName] = useState('')
  const [role, setRole] = useState<Role>('reviewer')
  const [password, setPassword] = useState('')
  const [creating, setCreating] = useState(false)
  const [resetFor, setResetFor] = useState<string | null>(null)
  const [resetValue, setResetValue] = useState('')
  const [busyId, setBusyId] = useState<string | null>(null)

  const load = useCallback(async () => {
    try {
      setUsers(await listUsers())
      setError(null)
    } catch (problem) {
      setError(errorMessage(problem))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  async function handleCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setNotice(null)
    if (password.length < MIN_PASSWORD) {
      setError(`The password must be at least ${MIN_PASSWORD} characters long.`)
      return
    }
    setError(null)
    setCreating(true)
    try {
      const created = await createUser({ email: email.trim(), name: name.trim(), role, password })
      setNotice(`User ${created.email} was created.`)
      setEmail('')
      setName('')
      setRole('reviewer')
      setPassword('')
      await load()
    } catch (problem) {
      setError(errorMessage(problem))
    } finally {
      setCreating(false)
    }
  }

  async function applyChange(user: ManagedUser, changes: { role?: Role; is_active?: boolean }) {
    setNotice(null)
    setError(null)
    setBusyId(user.id)
    try {
      const updated = await updateUser(user.id, changes)
      setUsers((current) => current.map((item) => (item.id === updated.id ? updated : item)))
    } catch (problem) {
      setError(errorMessage(problem))
    } finally {
      setBusyId(null)
    }
  }

  async function saveReset(user: ManagedUser) {
    setNotice(null)
    if (resetValue.length < MIN_PASSWORD) {
      setError(`The password must be at least ${MIN_PASSWORD} characters long.`)
      return
    }
    setError(null)
    setBusyId(user.id)
    try {
      await resetUserPassword(user.id, resetValue)
      setNotice(`The password of ${user.email} was changed.`)
      setResetFor(null)
      setResetValue('')
    } catch (problem) {
      setError(errorMessage(problem))
    } finally {
      setBusyId(null)
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold">Users</h1>

      {error && (
        <p role="alert" className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">
          {error}
        </p>
      )}
      {notice && (
        <p role="status" className="rounded-md border border-green-200 bg-green-50 px-3 py-2 text-sm text-green-800">
          {notice}
        </p>
      )}

      <form onSubmit={handleCreate} className="grid gap-4 rounded-lg border border-slate-200 bg-white p-4 md:grid-cols-2">
        <h2 className="text-base font-semibold md:col-span-2">Add a user</h2>
        <div>
          <label htmlFor="new-user-name" className="mb-1 block text-sm font-medium text-slate-700">
            Name
          </label>
          <input
            id="new-user-name"
            required
            maxLength={100}
            value={name}
            onChange={(event) => setName(event.target.value)}
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
          />
        </div>
        <div>
          <label htmlFor="new-user-email" className="mb-1 block text-sm font-medium text-slate-700">
            Email
          </label>
          <input
            id="new-user-email"
            type="email"
            required
            maxLength={254}
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
          />
        </div>
        <div>
          <label htmlFor="new-user-role" className="mb-1 block text-sm font-medium text-slate-700">
            Role
          </label>
          <select
            id="new-user-role"
            value={role}
            onChange={(event) => setRole(event.target.value as Role)}
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
          >
            <option value="reviewer">Reviewer</option>
            <option value="admin">Admin</option>
          </select>
        </div>
        <div>
          <label htmlFor="new-user-password" className="mb-1 block text-sm font-medium text-slate-700">
            Temporary password
          </label>
          <input
            id="new-user-password"
            type="password"
            autoComplete="new-password"
            required
            maxLength={128}
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
          />
          <p className="mt-1 text-xs text-slate-500">At least {MIN_PASSWORD} characters. Tell the user to change it after signing in.</p>
        </div>
        <div className="md:col-span-2">
          <button
            type="submit"
            disabled={creating}
            className="rounded-md bg-indigo-600 px-3 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-60"
          >
            {creating ? 'Creating...' : 'Create user'}
          </button>
        </div>
      </form>

      {loading ? (
        <p role="status" className="text-sm text-slate-600">
          Loading...
        </p>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
          <table className="min-w-full text-left text-sm">
            <thead className="border-b border-slate-200 bg-slate-50 text-slate-600">
              <tr>
                <th className="px-3 py-2 font-medium">Name</th>
                <th className="px-3 py-2 font-medium">Email</th>
                <th className="px-3 py-2 font-medium">Role</th>
                <th className="px-3 py-2 font-medium">Status</th>
                <th className="px-3 py-2 font-medium">Last sign-in</th>
                <th className="px-3 py-2 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map((user) => {
                const isSelf = user.id === auth.user?.id
                const busy = busyId === user.id
                return (
                  <tr key={user.id} className="border-b border-slate-100 align-top last:border-0">
                    <td className="px-3 py-2">
                      {user.name}
                      {isSelf ? ' (you)' : ''}
                    </td>
                    <td className="px-3 py-2">{user.email}</td>
                    <td className="px-3 py-2">
                      <select
                        aria-label={`Role for ${user.name}`}
                        value={user.role}
                        disabled={isSelf || busy}
                        onChange={(event) => void applyChange(user, { role: event.target.value as Role })}
                        className="rounded-md border border-slate-300 px-2 py-1 text-sm"
                      >
                        <option value="reviewer">Reviewer</option>
                        <option value="admin">Admin</option>
                      </select>
                    </td>
                    <td className="px-3 py-2">{user.is_active ? 'Active' : 'Deactivated'}</td>
                    <td className="px-3 py-2">{formatDate(user.last_login_at)}</td>
                    <td className="px-3 py-2">
                      <div className="flex flex-wrap items-center gap-2">
                        <button
                          type="button"
                          aria-label={`${user.is_active ? 'Deactivate' : 'Activate'} ${user.name}`}
                          disabled={isSelf || busy}
                          onClick={() => void applyChange(user, { is_active: !user.is_active })}
                          className="rounded-md border border-slate-300 px-2 py-1 text-xs font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50"
                        >
                          {user.is_active ? 'Deactivate' : 'Activate'}
                        </button>
                        {resetFor === user.id ? (
                          <>
                            <input
                              type="password"
                              aria-label={`New password for ${user.name}`}
                              autoComplete="new-password"
                              maxLength={128}
                              value={resetValue}
                              onChange={(event) => setResetValue(event.target.value)}
                              className="rounded-md border border-slate-300 px-2 py-1 text-xs"
                            />
                            <button
                              type="button"
                              aria-label={`Save new password for ${user.name}`}
                              disabled={busy}
                              onClick={() => void saveReset(user)}
                              className="rounded-md bg-indigo-600 px-2 py-1 text-xs font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
                            >
                              Save
                            </button>
                            <button
                              type="button"
                              onClick={() => {
                                setResetFor(null)
                                setResetValue('')
                              }}
                              className="rounded-md px-2 py-1 text-xs font-medium text-slate-700 hover:bg-slate-100"
                            >
                              Cancel
                            </button>
                          </>
                        ) : (
                          <button
                            type="button"
                            aria-label={`Reset password for ${user.name}`}
                            onClick={() => {
                              setResetFor(user.id)
                              setResetValue('')
                            }}
                            className="rounded-md border border-slate-300 px-2 py-1 text-xs font-medium text-slate-700 hover:bg-slate-50"
                          >
                            Reset password
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
