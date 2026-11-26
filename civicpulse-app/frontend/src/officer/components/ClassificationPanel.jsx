import { useState } from 'react'
import { officerApi } from '../api/officerApi'
import { formatConfidence, formatDateTime, formatSeverity } from '../lib/format'

export function ClassificationPanel({ complaintId, ai, corrections, issueTypes, onCorrected }) {
  const [issueType, setIssueType] = useState('')
  const [reason, setReason] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)

  const submit = async (event) => {
    event.preventDefault()
    setBusy(true)
    setError(null)
    try {
      await officerApi.correctClassification(complaintId, { issueType: issueType.trim(), reason: reason.trim() })
      setIssueType(''); setReason('')
      onCorrected?.()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="space-y-4 p-4 text-sm">
      <dl className="grid grid-cols-2 gap-x-4 gap-y-2">
        <dt className="text-muted">AI classification</dt>
        <dd className="font-medium">{ai.original_issue_type || '-'}</dd>
        <dt className="text-muted">Current issue type</dt>
        <dd className="font-medium">{ai.current_issue_type || '-'}{ai.corrected && ' (corrected by officer)'}</dd>
        <dt className="text-muted">AI confidence</dt>
        <dd>{formatConfidence(ai.confidence)}</dd>
        <dt className="text-muted">Severity</dt>
        <dd>{formatSeverity(ai.severity)}</dd>
      </dl>

      <form onSubmit={submit} className="space-y-3 border-t border-line pt-4">
        <p className="font-medium">Correct the classification</p>
        <div>
          <label htmlFor="cc-type" className="label">Correct issue type</label>
          <input id="cc-type" list="cc-types" className="field" value={issueType} onChange={(e) => setIssueType(e.target.value)} />
          <datalist id="cc-types">{issueTypes.map((t) => <option key={t} value={t} />)}</datalist>
        </div>
        <div>
          <label htmlFor="cc-reason" className="label">Reason (optional)</label>
          <input id="cc-reason" className="field" maxLength={500} value={reason} onChange={(e) => setReason(e.target.value)} />
        </div>
        {error && <p role="alert" className="rounded-md bg-high-tint px-3 py-2 text-high-text">{error}</p>}
        <button type="submit" className="btn-secondary" disabled={busy || issueType.trim().length < 2}>
          {busy ? 'Saving...' : 'Save correction'}
        </button>
      </form>

      {corrections.length > 0 && (
        <div className="border-t border-line pt-4">
          <p className="font-medium">Correction history</p>
          <ul className="mt-2 space-y-2">
            {corrections.map((c) => (
              <li key={c.id}>
                {c.old_issue_type || 'Unknown'} {'\u2192'} <strong>{c.new_issue_type}</strong>
                <span className="block text-muted">
                  {formatDateTime(c.created_at)}{c.officer_name ? ` by ${c.officer_name}` : ''}{c.reason ? ` - ${c.reason}` : ''}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
