interface Props {
  ok: boolean
  label: string
}

export default function StatusBadge({ ok, label }: Props) {
  const tone = ok ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'
  const dot = ok ? 'bg-emerald-600' : 'bg-amber-600'
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ${tone}`}>
      <span className={`h-1.5 w-1.5 rounded-full ${dot}`} aria-hidden="true" />
      {label}
    </span>
  )
}
