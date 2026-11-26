import { formatDateTime } from '../lib/format'
import { statusLabel } from '../lib/labels'
import { mediaUrl } from '../config'

/** Real status_history rows, oldest first. */
export function StatusTimeline({ history }) {
  if (!history?.length) {
    return <p className="px-4 py-6 text-sm text-muted">No status changes have been recorded yet.</p>
  }
  return (
    <ol className="divide-y divide-line">
      {history.map((h) => (
        <li key={h.id} className="px-4 py-3 text-sm">
          <p className="font-semibold">
            {h.old_status ? `${statusLabel(h.old_status)} \u2192 ${statusLabel(h.new_status)}` : statusLabel(h.new_status)}
          </p>
          <p className="text-muted">
            {formatDateTime(h.created_at)}
            {h.officer_name ? ` by ${h.officer_name}` : ''}
          </p>
          {h.comment && <p className="mt-1 whitespace-pre-line">{h.comment}</p>}
          {h.after_photo_url && (
            <a href={mediaUrl(h.after_photo_url)} target="_blank" rel="noreferrer" className="mt-1 inline-block text-civic underline">
              View after-photo
            </a>
          )}
        </li>
      ))}
    </ol>
  )
}
