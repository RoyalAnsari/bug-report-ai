interface Props {
  title: string
  message: string
}

export default function EmptyState({ title, message }: Props) {
  return (
    <div className="mt-6 rounded-lg border border-dashed border-slate-300 bg-white p-8 text-center">
      <p className="font-medium text-slate-900">{title}</p>
      <p className="mt-1 text-sm text-slate-600">{message}</p>
    </div>
  )
}
