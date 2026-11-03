import { useCallback, useState } from 'react'
import ClassMetricsChart from '../components/ClassMetricsChart'
import ClassMetricsTable from '../components/ClassMetricsTable'
import ConfusionMatrix from '../components/ConfusionMatrix'
import EmptyState from '../components/EmptyState'
import ErrorState from '../components/ErrorState'
import LoadingState from '../components/LoadingState'
import StatCard from '../components/StatCard'
import { useAsyncData } from '../hooks/useAsyncData'
import { formatScore, toClassRows, weakestClasses } from '../lib/evaluation'
import { formatDateTime, formatNumber } from '../lib/format'
import { getModel, getModels } from '../services/models'
import type { Evaluation, ModelDetail } from '../types/models'

const CONFIG_LABELS: [string, string][] = [
  ['model', 'Embedding model'],
  ['rows', 'Reports in the index'],
  ['embedding_dim', 'Embedding size'],
  ['score_type', 'Score type'],
  ['default_top_k', 'Default number of candidates'],
  ['default_threshold', 'Default minimum similarity'],
  ['created_utc', 'Index built'],
]

function EvaluationView({ evaluation, model }: { evaluation: Evaluation; model: ModelDetail }) {
  const rows = toClassRows(evaluation)
  const weakest = weakestClasses(rows)
  const training = model.training

  return (
    <>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard title="Macro F1" value={formatScore(evaluation.macro_f1)} hint="Every class counts the same" />
        <StatCard title="Macro precision" value={formatScore(evaluation.macro_precision)} />
        <StatCard title="Macro recall" value={formatScore(evaluation.macro_recall)} />
        <StatCard
          title="Reports evaluated"
          value={formatNumber(evaluation.rows)}
          hint={`${evaluation.split} set`}
        />
      </div>

      <div className="rounded-lg border border-slate-200 bg-white p-4">
        <h2 className="font-medium">Precision, recall and F1 for each severity</h2>
        <p className="mt-1 text-sm text-slate-600">
          {`The lowest F1 is for ${weakest.map((row) => `${row.label} (${formatScore(row.f1)})`).join(', ')}.`}
        </p>
        <div className="mt-4">
          <ClassMetricsChart rows={rows} />
        </div>
        <div className="mt-4">
          <ClassMetricsTable rows={rows} />
        </div>
      </div>

      <div className="rounded-lg border border-slate-200 bg-white p-4">
        <h2 className="font-medium">Confusion matrix</h2>
        <div className="mt-3">
          <ConfusionMatrix labels={evaluation.labels_order} matrix={evaluation.confusion_matrix} />
        </div>
      </div>

      {training && (
        <div className="rounded-lg border border-slate-200 bg-white p-4">
          <h2 className="font-medium">How it was trained</h2>
          <dl className="mt-3 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div>
              <dt className="text-sm text-slate-600">Random seed</dt>
              <dd className="mt-1 text-slate-900">{training.seed ?? '-'}</dd>
            </div>
            <div>
              <dt className="text-sm text-slate-600">Validation macro F1</dt>
              <dd className="mt-1 text-slate-900">{formatScore(training.validation_macro_f1)}</dd>
            </div>
            <div>
              <dt className="text-sm text-slate-600">Python</dt>
              <dd className="mt-1 text-slate-900">{training.library_versions?.python ?? '-'}</dd>
            </div>
            <div>
              <dt className="text-sm text-slate-600">scikit-learn</dt>
              <dd className="mt-1 text-slate-900">{training.library_versions?.scikit_learn ?? '-'}</dd>
            </div>
          </dl>
        </div>
      )}
    </>
  )
}

function NotMeasuredView({ model }: { model: ModelDetail }) {
  const config = model.config ?? {}
  const shown = CONFIG_LABELS.filter(([key]) => config[key] !== undefined && config[key] !== null)

  return (
    <>
      <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-amber-900">
        <h2 className="font-medium">Not measured</h2>
        <p className="mt-1 text-sm">{model.evaluation_note ?? 'No evaluation was saved for this model.'}</p>
      </div>
      {shown.length > 0 && (
        <div className="rounded-lg border border-slate-200 bg-white p-4">
          <h2 className="font-medium">Settings</h2>
          <dl className="mt-3 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {shown.map(([key, label]) => (
              <div key={key}>
                <dt className="text-sm text-slate-600">{label}</dt>
                <dd className="mt-1 break-all text-slate-900">
                  {key === 'created_utc' ? formatDateTime(String(config[key])) : String(config[key])}
                </dd>
              </div>
            ))}
          </dl>
        </div>
      )}
    </>
  )
}

function ModelDetailView({ model }: { model: ModelDetail }) {
  return (
    <div className="mt-6 space-y-6">
      <div className="rounded-lg border border-slate-200 bg-white p-4">
        <h2 className="font-medium">{model.name}</h2>
        <p className="mt-1 text-sm text-slate-600">{model.task}</p>
        <dl className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <dt className="text-sm text-slate-600">Version</dt>
            <dd className="mt-1 break-all text-slate-900">{model.version}</dd>
          </div>
          <div>
            <dt className="text-sm text-slate-600">Algorithm</dt>
            <dd className="mt-1 text-slate-900">{model.algorithm}</dd>
          </div>
          <div>
            <dt className="text-sm text-slate-600">Variant</dt>
            <dd className="mt-1 break-all text-slate-900">{model.variant ?? '-'}</dd>
          </div>
          <div>
            <dt className="text-sm text-slate-600">Registered</dt>
            <dd className="mt-1 text-slate-900">{formatDateTime(model.created_at)}</dd>
          </div>
        </dl>
      </div>

      {model.evaluation ? (
        <EvaluationView evaluation={model.evaluation} model={model} />
      ) : (
        <NotMeasuredView model={model} />
      )}
    </div>
  )
}

export default function ModelsPage() {
  const models = useAsyncData(getModels)
  const [selectedId, setSelectedId] = useState('')

  const list = models.data ?? []
  const selected =
    list.find((item) => item.id === selectedId) ?? list.find((item) => item.has_evaluation) ?? list[0] ?? null

  const loadDetail = useCallback(
    () => (selected ? getModel(selected.name, selected.version) : Promise.resolve(null)),
    [selected],
  )
  const detail = useAsyncData(loadDetail)
  const detailReady = detail.data && selected && detail.data.id === selected.id ? detail.data : null

  return (
    <section>
      <h1 className="text-2xl font-semibold">Model performance</h1>
      <p className="mt-1 text-sm text-slate-600">
        The numbers come from the evaluation that was saved when each model was registered. This page does not estimate
        anything itself.
      </p>

      {models.loading && !models.data && <LoadingState label="Loading models..." />}
      {models.error && <ErrorState message={models.error} onRetry={() => void models.reload()} />}
      {models.data && models.data.length === 0 && (
        <EmptyState
          title="No models are registered"
          message="Register the trained models first (python backend\register_models.py)."
        />
      )}

      {selected && (
        <>
          <div className="mt-6">
            <label htmlFor="model-select" className="block text-sm font-medium text-slate-700">
              Model
            </label>
            <select
              id="model-select"
              value={selected.id}
              onChange={(event) => setSelectedId(event.target.value)}
              className="mt-1 block rounded-md border border-slate-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              {list.map((item) => (
                <option key={item.id} value={item.id}>
                  {`${item.name} (${item.version})`}
                </option>
              ))}
            </select>
          </div>

          {detail.loading && !detailReady && <LoadingState label="Loading the evaluation..." />}
          {detail.error && <ErrorState message={detail.error} onRetry={() => void detail.reload()} />}
          {detailReady && <ModelDetailView model={detailReady} />}
        </>
      )}
    </section>
  )
}
