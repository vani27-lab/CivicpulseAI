import { useState } from 'react'
import { Link } from 'react-router-dom'
import { officerApi } from '../api/officerApi'
import { EmptyState, ErrorState, LoadingState } from '../components/States'
import { useAsync } from '../hooks/useAsync'
import { formatDateTime, shortId } from '../lib/format'

function CandidateCard({ candidate, onDone }) {
  const [busy, setBusy] = useState(null)
  const [error, setError] = useState(null)
  const [confirmingMerge, setConfirmingMerge] = useState(false)
  const a = candidate.complaint_id
  const b = candidate.candidate_complaint_id

  const act = async (kind) => {
    setBusy(kind)
    setError(null)
    try {
      await (kind === 'merge' ? officerApi.confirmMerge(candidate.id) : officerApi.rejectMerge(candidate.id))
      onDone()
    } catch (err) {
      setError(err.message)
      setConfirmingMerge(false)
    } finally {
      setBusy(null)
    }
  }

  return (
    <li className="space-y-3 px-4 py-4 text-sm">
      <p className="font-medium">
        <Link className="text-civic underline" to={`/officer/complaints/${a}`}>#{shortId(a)}</Link>
        {' and '}
        <Link className="text-civic underline" to={`/officer/complaints/${b}`}>#{shortId(b)}</Link>
      </p>
      <p className="text-muted">
        {candidate.similarity != null && `${Math.round(candidate.similarity * 100)}% visually similar`}
        {candidate.distance_m != null && `, ${Math.round(candidate.distance_m)} m apart`}
        {candidate.created_at && `, flagged ${formatDateTime(candidate.created_at)}`}
      </p>
      {candidate.reason && <p>{candidate.reason}</p>}
      {error && <p role="alert" className="rounded-md bg-high-tint px-3 py-2 text-high-text">{error}</p>}
      <div className="flex flex-wrap gap-2">
        {confirmingMerge ? (
          <>
            <button type="button" className="btn-primary" disabled={!!busy} onClick={() => act('merge')}>
              {busy === 'merge' ? 'Merging...' : 'Yes, merge these complaints'}
            </button>
            <button type="button" className="btn-secondary" disabled={!!busy} onClick={() => setConfirmingMerge(false)}>Cancel</button>
          </>
        ) : (
          <>
            <button type="button" className="btn-primary" disabled={!!busy} onClick={() => setConfirmingMerge(true)}>Confirm merge</button>
            <button type="button" className="btn-secondary" disabled={!!busy} onClick={() => act('reject')}>
              {busy === 'reject' ? 'Rejecting...' : 'Not a duplicate'}
            </button>
          </>
        )}
      </div>
    </li>
  )
}

export default function DuplicatesPage() {
  const [page, setPage] = useState(1)
  const list = useAsync((signal) => officerApi.duplicates({ status: 'pending', page, page_size: 20 }, signal), [page])
  const items = list.data?.items ?? []
  const total = list.data?.total ?? items.length

  return (
    <>
      <h1 className="text-2xl font-bold">Possible duplicates</h1>
      <p className="text-sm text-muted">Module 4 flags complaints that may describe the same issue. Review each pair before merging.</p>
      <section className="panel">
        {list.error ? <ErrorState error={list.error} onRetry={list.reload} />
          : list.loading && !list.data ? <LoadingState label="Loading duplicate candidates..." />
          : items.length === 0 ? <EmptyState title="No duplicates to review">New candidates appear here when the system finds similar complaints nearby.</EmptyState>
          : (
            <>
              <ul className="divide-y divide-line">
                {items.map((c) => <CandidateCard key={c.id} candidate={c} onDone={list.reload} />)}
              </ul>
              {total > 20 && (
                <div className="flex justify-between border-t border-line px-4 py-3">
                  <button type="button" className="btn-secondary" disabled={page <= 1} onClick={() => setPage(page - 1)}>Previous</button>
                  <button type="button" className="btn-secondary" disabled={page * 20 >= total} onClick={() => setPage(page + 1)}>Next</button>
                </div>
              )}
            </>
          )}
      </section>
    </>
  )
}
