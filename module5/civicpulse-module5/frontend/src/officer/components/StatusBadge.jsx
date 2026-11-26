import { STATUS_BADGE, statusLabel } from '../lib/labels'

export function StatusBadge({ status }) {
  return (
    <span className={`inline-flex rounded px-2 py-0.5 text-sm font-medium ${STATUS_BADGE[status] ?? 'bg-paper text-muted'}`}>
      {statusLabel(status)}
    </span>
  )
}
