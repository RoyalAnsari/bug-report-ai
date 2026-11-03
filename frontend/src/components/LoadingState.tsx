interface Props {
  label?: string
}

export default function LoadingState({ label = 'Loading...' }: Props) {
  return (
    <div role="status" className="flex items-center gap-3 py-4 text-slate-600">
      <span
        className="h-5 w-5 animate-spin rounded-full border-2 border-slate-300 border-t-indigo-600"
        aria-hidden="true"
      />
      <span>{label}</span>
    </div>
  )
}
