import { Link } from 'react-router-dom'
import { formatCoords, formatDate, shortId } from '../lib/format'
import { priorityStyle } from '../lib/labels'
import { PriorityBadge } from './PriorityBadge'
import { StatusBadge } from './StatusBadge'

const COLUMNS = [
  { key: 'id', label: 'Complaint ID' },
  { key: 'issue_type', label: 'Issue', sortable: true },
  { key: 'location', label: 'Location' },
  { key: 'department', label: 'Department', sortable: true },
  { key: 'report_count', label: 'Reports', sortable: true },
  { key: 'priority', label: 'Priority', sortable: true },
  { key: 'status', label: 'Status', sortable: true },
  { key: 'created_at', label: 'Submitted', sortable: true },
  { key: 'actions', label: 'Actions' },
]

export function ComplaintTable({ items, sortBy, sortDir, onSort }) {
  const ariaSort = (key) => (sortBy === key ? (sortDir === 'asc' ? 'ascending' : 'descending') : 'none')

  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[60rem] text-left text-sm">
        <thead className="border-y border-line bg-paper text-muted">
          <tr>
            {COLUMNS.map((col) => (
              <th key={col.key} scope="col" aria-sort={col.sortable ? ariaSort(col.key) : undefined} className="px-3 py-2 font-semibold">
                {col.sortable ? (
                  <button type="button" onClick={() => onSort(col.key)} className="inline-flex items-center gap-1 font-semibold hover:text-ink">
                    {col.label}
                    <span aria-hidden="true">{sortBy === col.key ? (sortDir === 'asc' ? '\u25B2' : '\u25BC') : ''}</span>
                  </button>
                ) : col.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {items.map((c) => (
            <tr key={c.id} className="border-b border-line align-top hover:bg-civic-soft/40" data-testid="complaint-row">
              <td className="relative py-2.5 pl-4 pr-3 font-medium">
                <span aria-hidden="true" className={`absolute inset-y-0 left-0 w-1 ${priorityStyle(c.priority_band).rail}`} />
                <span title={c.id}>{shortId(c.id)}</span>
              </td>
              <td className="px-3 py-2.5">{c.issue_type || '-'}</td>
              <td className="px-3 py-2.5 text-muted">{formatCoords(c.latitude, c.longitude)}</td>
              <td className="px-3 py-2.5">{c.department_name || 'Unassigned'}</td>
              <td className="px-3 py-2.5 tabular-nums">{c.report_count}</td>
              <td className="px-3 py-2.5"><PriorityBadge band={c.priority_band} score={c.priority_score} /></td>
              <td className="px-3 py-2.5"><StatusBadge status={c.status} /></td>
              <td className="px-3 py-2.5 whitespace-nowrap">{formatDate(c.created_at)}</td>
              <td className="px-3 py-2.5">
                <Link to={`/officer/complaints/${c.id}`} className="font-semibold text-civic underline underline-offset-2">
                  Open<span className="sr-only"> complaint {shortId(c.id)}</span>
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
