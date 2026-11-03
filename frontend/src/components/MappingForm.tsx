import { FIELD_LABELS, FIELD_ORDER } from '../lib/upload'
import type { ColumnMapping, FieldName } from '../types/upload'

interface Props {
  headers: string[]
  mapping: ColumnMapping
  onChange: (field: FieldName, column: string | null) => void
  disabled?: boolean
}

export default function MappingForm({ headers, mapping, onChange, disabled = false }: Props) {
  return (
    <div className="grid gap-4 sm:grid-cols-2">
      {FIELD_ORDER.map((field) => {
        const id = `mapping-${field}`
        return (
          <div key={field}>
            <label htmlFor={id} className="block text-sm font-medium text-slate-700">
              {FIELD_LABELS[field]}
            </label>
            <select
              id={id}
              value={mapping[field] ?? ''}
              disabled={disabled}
              onChange={(event) => onChange(field, event.target.value || null)}
              className="mt-1 block w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50"
            >
              <option value="">{field === 'text' ? 'Choose a column' : 'Not used'}</option>
              {headers.map((header) => (
                <option key={header} value={header}>
                  {header}
                </option>
              ))}
            </select>
          </div>
        )
      })}
    </div>
  )
}
