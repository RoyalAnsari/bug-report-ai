export function formatNumber(value: number): string {
  return value.toLocaleString('en-US')
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '-'
  return date.toLocaleString('en-GB', { dateStyle: 'medium', timeStyle: 'short' })
}
