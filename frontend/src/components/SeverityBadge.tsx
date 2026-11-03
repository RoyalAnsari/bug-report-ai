interface Props {
  label: string
}

const STYLES: Record<string, string> = {
  blocker: 'bg-red-100 text-red-800',
  critical: 'bg-orange-100 text-orange-800',
  major: 'bg-amber-100 text-amber-800',
  normal: 'bg-sky-100 text-sky-800',
  minor: 'bg-slate-200 text-slate-800',
  trivial: 'bg-zinc-100 text-zinc-700',
  unlabeled: 'bg-white text-slate-600 ring-1 ring-slate-300',
}

export default function SeverityBadge({ label }: Props) {
  const style = STYLES[label] ?? 'bg-slate-100 text-slate-700'
  return <span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-medium ${style}`}>{label}</span>
}
