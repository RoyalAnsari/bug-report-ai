import { useRef, useState } from 'react'
import type { ChangeEvent, DragEvent } from 'react'

interface Props {
  onFile: (file: File) => void
  disabled?: boolean
}

export default function FileDropzone({ onFile, disabled = false }: Props) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [dragging, setDragging] = useState(false)

  function handleChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    event.target.value = '' // so the same file can be chosen again
    if (file) onFile(file)
  }

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault()
    setDragging(false)
    if (disabled) return
    const file = event.dataTransfer.files?.[0]
    if (file) onFile(file)
  }

  function handleDragOver(event: DragEvent<HTMLDivElement>) {
    event.preventDefault()
    if (!disabled) setDragging(true)
  }

  const tone = dragging ? 'border-indigo-500 bg-indigo-50' : 'border-slate-300 bg-white'

  return (
    <div
      data-testid="dropzone"
      onDragOver={handleDragOver}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      className={`rounded-lg border-2 border-dashed p-8 text-center ${tone}`}
    >
      <p className="font-medium text-slate-900">Drag and drop a CSV file here</p>
      <p className="mt-1 text-sm text-slate-600">or</p>
      <input
        ref={inputRef}
        type="file"
        accept=".csv,text/csv"
        aria-label="CSV file"
        className="sr-only"
        tabIndex={-1}
        disabled={disabled}
        onChange={handleChange}
      />
      <button
        type="button"
        disabled={disabled}
        onClick={() => inputRef.current?.click()}
        className="mt-2 rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:opacity-50"
      >
        Choose file
      </button>
      <p className="mt-3 text-xs text-slate-500">Only .csv files, up to 5 MB.</p>
    </div>
  )
}
