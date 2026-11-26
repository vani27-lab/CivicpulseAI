import { useState } from 'react'
import { officerApi } from '../api/officerApi'
import { formatDateTime } from '../lib/format'

/** Lets an officer move reports that were merged by mistake into a new complaint (executed by Module 4). */
export function SplitPanel({ complaintId, reports, onSplit }) {
  const [selected, setSelected] = useState([])
  const [reason, setReason] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const [confirming, setConfirming] = useState(false)

  if (reports.length < 2) {
    return <p className="p-4 text-sm text-muted">This complaint has a single report, so there is nothing to split.</p>
  }

  const toggle = (id) => setSelected((s) => (s.includes(id) ? s.filter((x) => x !== id) : [...s, id]))
  const allSelected = selected.length === reports.length

  const run = async () => {
    setBusy(true)
    setError(null)
    try {
      await officerApi.split(complaintId, { reportIds: selected, reason: reason.trim() })
      setSelected([]); setReason(''); setConfirming(false)
      onSplit?.()
    } catch (err) {
      setError(err.message)
      setConfirming(false)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="space-y-3 p-4 text-sm">
      <p className="text-muted">Select the reports that do not belong to this complaint. They move to a new complaint.</p>
      <ul className="space-y-1">
        {reports.map((r, i) => (
          <li key={r.id}>
            <label className="flex items-start gap-2">
              <input type="checkbox" className="mt-1" checked={selected.includes(r.id)} onChange={() => toggle(r.id)} />
              <span>Report {i + 1}, {formatDateTime(r.created_at)}
                <span className="block text-muted">{r.translated_description || r.original_description || 'No description'}</span>
              </span>
            </label>
          </li>
        ))}
      </ul>
      <div>
        <label htmlFor="sp-reason" className="label">Why are these reports separate?</label>
        <input id="sp-reason" className="field" maxLength={500} value={reason} onChange={(e) => setReason(e.target.value)} />
      </div>
      {allSelected && <p className="text-high-text">Leave at least one report on this complaint.</p>}
      {error && <p role="alert" className="rounded-md bg-high-tint px-3 py-2 text-high-text">{error}</p>}
      {confirming ? (
        <div className="flex gap-2">
          <button type="button" className="btn-danger" onClick={run} disabled={busy}>{busy ? 'Splitting...' : `Confirm split of ${selected.length}`}</button>
          <button type="button" className="btn-secondary" onClick={() => setConfirming(false)} disabled={busy}>Cancel</button>
        </div>
      ) : (
        <button type="button" className="btn-secondary" disabled={!selected.length || allSelected || reason.trim().length < 3}
                onClick={() => setConfirming(true)}>
          Split selected reports
        </button>
      )}
    </div>
  )
}
