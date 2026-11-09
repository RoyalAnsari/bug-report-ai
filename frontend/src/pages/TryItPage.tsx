import { useState } from 'react'
import type { FormEvent } from 'react'
import { errorMessage } from '../services/api'
import { triageReport } from '../services/triage'
import type { TriageResult } from '../types/triage'

const EXAMPLES = [
  'Crash when saving a file with a very long name',
  'Typo in the preferences dialog',
  'Password reset token can be guessed by an attacker',
]

const SEVERITY_STYLE: Record<string, string> = {
  blocker: 'bg-red-100 text-red-800',
  critical: 'bg-orange-100 text-orange-800',
  major: 'bg-amber-100 text-amber-800',
  normal: 'bg-slate-200 text-slate-800',
  minor: 'bg-sky-100 text-sky-800',
  trivial: 'bg-emerald-100 text-emerald-800',
}

export default function TryItPage() {
  const [text, setText] = useState('')
  const [project, setProject] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<TriageResult | null>(null)

  const canSubmit = text.trim().length >= 3 && !loading

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!canSubmit) return
    setLoading(true)
    setError(null)
    try {
      setResult(await triageReport({ text: text.trim(), project: project.trim() || null }))
    } catch (problem) {
      setResult(null)
      setError(errorMessage(problem))
    } finally {
      setLoading(false)
    }
  }

  const scores = result ? Object.entries(result.severity.scores).sort((a, b) => b[1] - a[1]) : []

  return (
    <div className="max-w-3xl space-y-6">
      <div>
        <h1 className="text-xl font-semibold">Try it</h1>
        <p className="mt-1 text-sm text-slate-600">
          Write a bug report title. You get a suggested severity, how sure the model is, and similar earlier bugs.
          Nothing is saved.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4 rounded-lg border border-slate-200 bg-white p-4">
        <div>
          <label htmlFor="try-text" className="mb-1 block text-sm font-medium text-slate-700">
            Bug report title
          </label>
          <textarea
            id="try-text"
            rows={3}
            maxLength={2000}
            value={text}
            onChange={(event) => setText(event.target.value)}
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
          />
          <div className="mt-2 flex flex-wrap gap-2">
            {EXAMPLES.map((example) => (
              <button
                key={example}
                type="button"
                onClick={() => setText(example)}
                className="rounded-md border border-slate-300 px-2 py-1 text-xs text-slate-700 hover:bg-slate-50"
              >
                {example}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label htmlFor="try-project" className="mb-1 block text-sm font-medium text-slate-700">
            Project (optional)
          </label>
          <input
            id="try-project"
            maxLength={100}
            value={project}
            onChange={(event) => setProject(event.target.value)}
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
          />
        </div>

        <button
          type="submit"
          disabled={!canSubmit}
          className="rounded-md bg-indigo-600 px-3 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-60"
        >
          {loading ? 'Analysing...' : 'Analyse'}
        </button>
      </form>

      {error && (
        <p role="alert" className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">
          {error}
        </p>
      )}

      {result && (
        <div className="space-y-4">
          <section className="rounded-lg border border-slate-200 bg-white p-4">
            <h2 className="text-base font-semibold">Suggested severity</h2>
            <div className="mt-3 flex flex-wrap items-center gap-3">
              <span
                data-testid="severity-label"
                className={`rounded-md px-3 py-1 text-sm font-semibold capitalize ${
                  SEVERITY_STYLE[result.severity.label] ?? 'bg-slate-200 text-slate-800'
                }`}
              >
                {result.severity.label}
              </span>
              <span className="text-sm text-slate-600">Confidence gap: {result.severity.margin.toFixed(2)}</span>
            </div>
            {result.severity.needs_review && (
              <p role="status" className="mt-3 rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900">
                Needs review: the model is not sure about this one. A person should check it.
              </p>
            )}
            <table className="mt-4 w-full max-w-xs text-sm">
              <caption className="mb-1 text-left text-xs text-slate-500">Score for each class</caption>
              <tbody>
                {scores.map(([label, score]) => (
                  <tr key={label} className="border-b border-slate-100 last:border-0">
                    <td className="py-1 capitalize">{label}</td>
                    <td className="py-1 text-right tabular-nums">{score.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-4">
            <h2 className="text-base font-semibold">Similar earlier bugs</h2>
            {result.similar.length === 0 ? (
              <p className="mt-2 text-sm text-slate-600">No similar earlier bug was found (similarity 0.5 or more).</p>
            ) : (
              <ul className="mt-3 space-y-3">
                {result.similar.map((hit) => (
                  <li key={hit.bug_id} className="text-sm">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-medium tabular-nums">{Math.round(hit.similarity * 100)}% similar</span>
                      {hit.likely_duplicate && (
                        <span className="rounded bg-indigo-100 px-2 py-0.5 text-xs font-medium text-indigo-800">
                          Likely duplicate
                        </span>
                      )}
                      <span className="text-xs text-slate-500">
                        Bug {hit.bug_id}, {hit.project}
                      </span>
                    </div>
                    <p className="mt-1 text-slate-800">{hit.text}</p>
                  </li>
                ))}
              </ul>
            )}
            <p className="mt-3 text-xs text-slate-500">
              The earlier bugs come from the public Bugzilla and Eclipse data, where every bug was marked fixed.
            </p>
          </section>

          <p className="text-xs text-slate-500">
            This is a suggestion for a person to confirm, not a decision. Model: {result.model_version}.
          </p>
        </div>
      )}
    </div>
  )
}
