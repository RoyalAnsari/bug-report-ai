import { useState } from 'react'
import ErrorState from '../components/ErrorState'
import LoadingState from '../components/LoadingState'
import StatusBadge from '../components/StatusBadge'
import { useAsyncData } from '../hooks/useAsyncData'
import { FIELDS, LIMITS, toForm, validateForm } from '../lib/settings'
import type { FieldName, FormValues } from '../lib/settings'
import { errorMessage } from '../services/api'
import { getSettings, resetSettings, saveSettings } from '../services/settings'

interface FieldProps {
  field: FieldName
  label: string
  help: string
  value: string
  error?: string
  defaultText: string
  onChange: (field: FieldName, value: string) => void
}

function NumberField({ field, label, help, value, error, defaultText, onChange }: FieldProps) {
  const id = `setting-${field}`
  const limit = LIMITS[field]
  return (
    <div>
      <label htmlFor={id} className="block text-sm font-medium text-slate-700">
        {label}
      </label>
      <input
        id={id}
        type="number"
        inputMode="decimal"
        min={limit.min}
        max={limit.max}
        step={limit.step}
        value={value}
        aria-invalid={Boolean(error)}
        aria-describedby={`${id}-help`}
        onChange={(event) => onChange(field, event.target.value)}
        className="mt-1 block w-40 rounded-md border border-slate-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
      />
      {error && <p className="mt-1 text-sm text-red-700">{error}</p>}
      <p id={`${id}-help`} className="mt-1 text-sm text-slate-600">
        {help}
      </p>
      <p className="mt-1 text-xs text-slate-500">{`Default: ${defaultText}`}</p>
    </div>
  )
}

export default function SettingsPage() {
  const settings = useAsyncData(getSettings)
  const [draft, setDraft] = useState<FormValues | null>(null)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)

  const server = settings.data
  const serverForm = server ? toForm(server.values) : null
  const form = draft ?? serverForm
  const { values, errors } = form ? validateForm(form) : { values: null, errors: {} }
  const dirty = Boolean(draft && serverForm && FIELDS.some((field) => draft[field] !== serverForm[field]))

  function change(field: FieldName, value: string) {
    if (!form) return
    setMessage(null)
    setActionError(null)
    setDraft({ ...form, [field]: value })
  }

  async function handleSave() {
    if (!values) return
    setSaving(true)
    setMessage(null)
    setActionError(null)
    try {
      await saveSettings(values)
      await settings.reload()
      setDraft(null)
      setMessage('Settings saved.')
    } catch (e) {
      setActionError(errorMessage(e))
    } finally {
      setSaving(false)
    }
  }

  async function handleReset() {
    setSaving(true)
    setMessage(null)
    setActionError(null)
    try {
      await resetSettings()
      await settings.reload()
      setDraft(null)
      setMessage('Settings were reset to the defaults.')
    } catch (e) {
      setActionError(errorMessage(e))
    } finally {
      setSaving(false)
    }
  }

  function handleUndo() {
    setDraft(null)
    setMessage(null)
    setActionError(null)
  }

  const outlineButton =
    'rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50'

  return (
    <section>
      <h1 className="text-2xl font-semibold">Settings</h1>
      <p className="mt-1 text-sm text-slate-600">
        Settings are saved in the database and stay after the backend is restarted.
      </p>

      {settings.loading && !server && <LoadingState label="Loading settings..." />}
      {settings.error && <ErrorState message={settings.error} onRetry={() => void settings.reload()} />}

      {server && form && (
        <div className="mt-6 space-y-6">
          <div className="rounded-lg border border-slate-200 bg-white p-4">
            <h2 className="font-medium">Model settings</h2>
            <div className="mt-4 grid gap-6 md:grid-cols-3">
              <NumberField
                field="review_margin"
                label="Review margin"
                help="A prediction is marked Needs review when the gap between its best and second best score is below this value. It applies to new predictions only. The default has not been tuned on validation data."
                value={form.review_margin}
                error={errors.review_margin}
                defaultText={String(server.defaults.review_margin)}
                onChange={change}
              />
              <NumberField
                field="duplicate_threshold"
                label="Minimum similarity for duplicates"
                help="Where Find possible duplicates starts. It is a cosine similarity score, not a probability. The default has not been tested against labelled duplicates."
                value={form.duplicate_threshold}
                error={errors.duplicate_threshold}
                defaultText={String(server.defaults.duplicate_threshold)}
                onChange={change}
              />
              <NumberField
                field="duplicate_top_k"
                label="Candidates to show for duplicates"
                help="How many possible duplicates are shown for one report."
                value={form.duplicate_top_k}
                error={errors.duplicate_top_k}
                defaultText={String(server.defaults.duplicate_top_k)}
                onChange={change}
              />
            </div>

            <div className="mt-6 flex flex-wrap items-center gap-3">
              <button
                type="button"
                onClick={() => void handleSave()}
                disabled={saving || !dirty || values === null}
                className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:opacity-50"
              >
                {saving ? 'Saving...' : 'Save settings'}
              </button>
              <button type="button" onClick={handleUndo} disabled={saving || !dirty} className={outlineButton}>
                Undo changes
              </button>
              <button type="button" onClick={() => void handleReset()} disabled={saving} className={outlineButton}>
                Reset to defaults
              </button>
            </div>

            {message && (
              <p className="mt-3 text-sm text-emerald-800" aria-live="polite">
                {message}
              </p>
            )}
            {actionError && <ErrorState message={actionError} />}
          </div>

          <div className="rounded-lg border border-slate-200 bg-white p-4">
            <h2 className="font-medium">Application</h2>
            <p className="mt-1 text-sm text-slate-600">These values are set when the backend starts. They cannot be changed here.</p>
            <dl className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <div>
                <dt className="text-sm text-slate-600">API version</dt>
                <dd className="mt-1 text-slate-900">{server.application.api_version}</dd>
              </div>
              <div>
                <dt className="text-sm text-slate-600">Database</dt>
                <dd className="mt-1 text-slate-900">{server.application.database}</dd>
              </div>
              <div>
                <dt className="text-sm text-slate-600">Allowed origins</dt>
                <dd className="mt-1 break-all text-slate-900">{server.application.cors_origins.join(', ')}</dd>
              </div>
              <div>
                <dt className="text-sm text-slate-600">Models</dt>
                <dd className="mt-1 flex flex-wrap gap-2">
                  <StatusBadge
                    ok={server.application.models_loaded.severity}
                    label={`Severity model: ${server.application.models_loaded.severity ? 'loaded' : 'not loaded'}`}
                  />
                  <StatusBadge
                    ok={server.application.models_loaded.duplicates}
                    label={`Duplicate model: ${server.application.models_loaded.duplicates ? 'loaded' : 'not loaded'}`}
                  />
                </dd>
              </div>
            </dl>
          </div>
        </div>
      )}
    </section>
  )
}
