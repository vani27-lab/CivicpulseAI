import { useEffect, useMemo, useState } from 'react'
import { officerApi } from '../api/officerApi'
import { statusLabel } from '../lib/labels'

export const MAX_PHOTO_BYTES = 8 * 1024 * 1024
const PHOTO_TYPES = ['image/jpeg', 'image/png', 'image/webp']

/**
 * The options come from the server (`allowedNextStatuses`), so workflow rules live in one place.
 * Client-side photo checks are only for quicker feedback; the backend validates again.
 */
export function StatusUpdateForm({ complaintId, currentStatus, allowedNextStatuses, canOverride, onUpdated }) {
  const [newStatus, setNewStatus] = useState('')
  const [comment, setComment] = useState('')
  const [photo, setPhoto] = useState(null)
  const [override, setOverride] = useState(false)
  const [overrideReason, setOverrideReason] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const [done, setDone] = useState(null)

  const preview = useMemo(() => (photo ? URL.createObjectURL(photo) : null), [photo])
  useEffect(() => () => { if (preview) URL.revokeObjectURL(preview) }, [preview])

  const allStatuses = ['submitted', 'assigned', 'in_progress', 'resolved', 'rejected'].filter((s) => s !== currentStatus)
  const options = override ? allStatuses : allowedNextStatuses
  const resolving = newStatus === 'resolved'
  const needsPhoto = resolving && !override
  const needsComment = newStatus === 'rejected' && !override

  const photoProblem = (file) => {
    if (!file) return null
    if (!PHOTO_TYPES.includes(file.type)) return 'Choose a JPEG, PNG or WebP photo.'
    if (file.size > MAX_PHOTO_BYTES) return 'The photo must be 8 MB or smaller.'
    return null
  }

  const pickPhoto = (e) => {
    const file = e.target.files?.[0] ?? null
    const problem = photoProblem(file)
    setError(problem)
    setPhoto(problem ? null : file)
  }

  const invalid =
    !newStatus ||
    (needsPhoto && !photo) ||
    (needsComment && !comment.trim()) ||
    (override && overrideReason.trim().length < 5)

  const submit = async (event) => {
    event.preventDefault()
    if (invalid) return
    setBusy(true)
    setError(null)
    setDone(null)
    try {
      const result = await officerApi.updateStatus(complaintId, {
        newStatus,
        comment: comment.trim(),
        photo: resolving ? photo : null,
        adminOverride: override,
        overrideReason,
      })
      setDone(`Status changed to ${statusLabel(result.new_status)}.`)
      setNewStatus(''); setComment(''); setPhoto(null); setOverride(false); setOverrideReason('')
      onUpdated?.(result)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  if (!options.length && !canOverride) {
    return <p className="p-4 text-sm text-muted">This complaint is {statusLabel(currentStatus)}. No further status changes are available.</p>
  }

  return (
    <form onSubmit={submit} className="space-y-4 p-4" noValidate>
      <div>
        <label htmlFor="su-status" className="label">Move to</label>
        <select id="su-status" className="field" value={newStatus} onChange={(e) => { setNewStatus(e.target.value); setError(null) }}>
          <option value="">Select a status</option>
          {options.map((s) => <option key={s} value={s}>{statusLabel(s)}</option>)}
        </select>
      </div>

      {resolving && (
        <div>
          <label htmlFor="su-photo" className="label">After-photo {needsPhoto ? '(required)' : '(optional with override)'}</label>
          <input id="su-photo" type="file" accept={PHOTO_TYPES.join(',')} onChange={pickPhoto} className="field" />
          {preview && <img src={preview} alt="Selected after-photo preview" className="mt-2 max-h-40 rounded-md border border-line" />}
        </div>
      )}

      <div>
        <label htmlFor="su-comment" className="label">Comment {needsComment ? '(required)' : '(optional)'}</label>
        <textarea id="su-comment" rows={3} maxLength={1000} className="field" value={comment} onChange={(e) => setComment(e.target.value)} />
        <p className="mt-1 text-xs text-muted">Citizens can see this comment in their tracking timeline.</p>
      </div>

      {canOverride && (
        <fieldset className="rounded-md border border-line p-3">
          <legend className="px-1 text-sm font-medium">Admin override</legend>
          <label className="flex items-start gap-2 text-sm">
            <input type="checkbox" checked={override} onChange={(e) => setOverride(e.target.checked)} className="mt-1" />
            <span>Skip workflow and evidence rules. The reason is recorded in the history.</span>
          </label>
          {override && (
            <div className="mt-2">
              <label htmlFor="su-reason" className="label">Reason for override</label>
              <input id="su-reason" className="field" value={overrideReason} onChange={(e) => setOverrideReason(e.target.value)} />
            </div>
          )}
        </fieldset>
      )}

      {error && <p role="alert" className="rounded-md bg-high-tint px-3 py-2 text-sm text-high-text">{error}</p>}
      {done && <p role="status" className="rounded-md bg-low-tint px-3 py-2 text-sm text-low-text">{done}</p>}

      <button type="submit" className="btn-primary" disabled={invalid || busy}>
        {busy ? 'Saving...' : resolving ? 'Resolve complaint' : 'Update status'}
      </button>
    </form>
  )
}
