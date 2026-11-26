import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { officerApi } from '../api/officerApi'
import { ClassificationPanel } from '../components/ClassificationPanel'
import { LocationMap } from '../components/LocationMap'
import { PriorityBadge } from '../components/PriorityBadge'
import { PriorityExplanation } from '../components/PriorityExplanation'
import { SplitPanel } from '../components/SplitPanel'
import { StatusBadge } from '../components/StatusBadge'
import { StatusTimeline } from '../components/StatusTimeline'
import { StatusUpdateForm } from '../components/StatusUpdateForm'
import { ErrorState, LoadingState } from '../components/States'
import { mediaUrl } from '../config'
import { useAsync } from '../hooks/useAsync'
import { formatConfidence, formatCoords, formatDateTime, formatSeverity, shortId } from '../lib/format'

const Panel = ({ title, children }) => (
  <section className="panel"><h2 className="panel-title">{title}</h2>{children}</section>
)

function ImageWithFallback({ src, alt, emptyText, caption }) {
  const [failed, setFailed] = useState(false)
  const url = mediaUrl(src)

  return (
    <figure className="min-w-0">
      {url && !failed ? (
        <img
          src={url}
          alt={alt}
          className="w-full max-h-80 rounded-md border border-line object-cover"
          onError={() => setFailed(true)}
        />
      ) : (
        <div className="rounded-md border border-dashed border-line p-6 text-center text-sm text-muted bg-[#EDE8E0]">
          <p className="font-medium text-ink">{failed ? 'Image file not found on server' : emptyText}</p>
          {failed && <p className="mt-1 text-xs text-muted">The photo file could not be retrieved from storage.</p>}
        </div>
      )}
      <figcaption className="mt-1.5 text-xs font-mono uppercase tracking-wider text-muted">{caption}</figcaption>
    </figure>
  )
}

export default function ComplaintDetailPage() {
  const { id } = useParams()
  const detail = useAsync((signal) => officerApi.complaint(id, signal), [id])
  const options = useAsync((signal) => officerApi.filterOptions(signal), [])

  if (detail.error && !detail.data) {
    return (
      <>
        <Link to="/officer" className="text-civic underline">Back to complaints</Link>
        <ErrorState error={detail.error} onRetry={detail.reload} />
      </>
    )
  }
  if (!detail.data) return <LoadingState label="Loading complaint..." />

  const c = detail.data
  const primary = c.reports[0]

  return (
    <>
      <Link to="/officer" className="text-sm text-civic underline">Back to complaints</Link>
      <header className="flex flex-wrap items-center gap-3">
        <h1 className="text-2xl font-bold">{c.issue_type || 'Complaint'} <span className="font-medium text-muted">#{shortId(c.id)}</span></h1>
        <StatusBadge status={c.status} />
        <PriorityBadge band={c.priority.band} score={c.priority.score} />
      </header>
      <p className="text-sm text-muted">Full ID {c.id}. {c.department_name ? `Assigned to ${c.department_name}.` : 'No department assigned yet.'}</p>
      {detail.error && <ErrorState error={detail.error} onRetry={detail.reload} />}

      <div className="grid gap-4 lg:grid-cols-3">
        <div className="space-y-4 lg:col-span-2">
          <Panel title="Evidence">
            <div className="grid gap-4 p-4 sm:grid-cols-2">
              <ImageWithFallback
                src={c.before_photo_url}
                alt="Before: photo submitted by the citizen"
                emptyText="No photo was submitted."
                caption="Before (citizen photo)"
              />
              <ImageWithFallback
                src={c.after_photo_url}
                alt="After: photo uploaded by the officer"
                emptyText="No after-photo yet. It is required to resolve this complaint."
                caption="After (officer photo)"
              />
            </div>
          </Panel>

          <Panel title="Citizen reports">
            <p className="px-4 pt-3 text-sm text-muted">{c.report_count} citizen report{c.report_count === 1 ? '' : 's'} merged into this complaint.</p>
            <ul className="divide-y divide-line">
              {c.reports.map((r, i) => (
                <li key={r.id} className="space-y-2 px-4 py-3 text-sm">
                  <p className="font-medium">Report {i + 1} <span className="font-normal text-muted">{formatDateTime(r.created_at)}</span></p>
                  <div className="grid gap-3 sm:grid-cols-2">
                    <div><p className="text-muted">Original description</p><p className="whitespace-pre-line">{r.original_description || '-'}</p></div>
                    <div><p className="text-muted">English translation</p><p className="whitespace-pre-line">{r.translated_description || 'Not available'}</p></div>
                  </div>
                  <p className="text-muted">
                    GPS {formatCoords(r.latitude, r.longitude)}, accuracy {r.gps_accuracy != null ? `${Math.round(r.gps_accuracy)} m` : '-'};
                    {' '}AI confidence {formatConfidence(r.ai_confidence)}, severity {formatSeverity(r.ai_severity)}
                  </p>
                </li>
              ))}
            </ul>
          </Panel>

          <Panel title="Status history"><StatusTimeline history={c.history} /></Panel>

          {c.duplicate_candidates.length > 0 && (
            <Panel title="Possible duplicates">
              <ul className="divide-y divide-line text-sm">
                {c.duplicate_candidates.map((d) => (
                  <li key={d.id} className="px-4 py-3">
                    Similar to <Link className="text-civic underline" to={`/officer/complaints/${d.candidate_complaint_id || d.complaint_id}`}>
                      #{shortId(d.candidate_complaint_id || d.complaint_id)}</Link>
                    {d.similarity != null && `, ${Math.round(d.similarity * 100)}% similar`}
                    {d.distance_m != null && `, ${Math.round(d.distance_m)} m apart`}
                  </li>
                ))}
              </ul>
              <p className="px-4 pb-3 text-sm"><Link className="text-civic underline" to="/officer/duplicates">Review in the duplicates queue</Link></p>
            </Panel>
          )}
        </div>

        <div className="space-y-4">
          <Panel title="Update status">
            <StatusUpdateForm complaintId={c.id} currentStatus={c.status} allowedNextStatuses={c.allowed_next_statuses}
                              canOverride={c.can_override} onUpdated={detail.reload} />
          </Panel>
          <Panel title="Priority">
            <div className="space-y-3 p-4">
              <PriorityBadge band={c.priority.band} score={c.priority.score} />
              {(c.priority.is_emergency || c.is_emergency) && (
                <div className="rounded-md border border-red-500 bg-red-100 p-2.5 text-xs font-bold text-red-900">
                  EMERGENCY ESCALATION ACTIVE: Immediate public safety or emergency facility access threat.
                </div>
              )}
              {c.priority.nearest_facility_name && (
                <div className="rounded-md bg-paper p-3 text-xs border border-line">
                  <span className="font-semibold text-muted uppercase tracking-wider block">Nearest Important Facility</span>
                  <p className="mt-1 font-medium text-ink text-sm">{c.priority.nearest_facility_name} ({c.priority.nearest_facility_type})</p>
                  <p className="text-muted">{Math.round(c.priority.nearest_facility_distance_m)} metres away</p>
                </div>
              )}
              <PriorityExplanation reasons={c.priority.reasons} />
            </div>
          </Panel>
          {((c.nearby_facilities && c.nearby_facilities.length > 0) || (c.priority?.nearby_facilities && c.priority.nearby_facilities.length > 0)) && (
            <Panel title="Nearby Critical Facilities">
              <div className="p-4 space-y-2 text-xs">
                {(c.nearby_facilities || c.priority?.nearby_facilities || []).slice(0, 5).map((f, i) => (
                  <div key={i} className="flex items-center justify-between border-b border-line pb-2">
                    <div>
                      <span className="font-medium text-ink">{f.name}</span>
                      <span className="ml-2 rounded bg-paper px-1.5 py-0.5 text-[10px] text-muted uppercase font-mono">{f.type}</span>
                    </div>
                    <span className="font-mono text-muted">{Math.round(f.distance_m)} m</span>
                  </div>
                ))}
              </div>
            </Panel>
          )}
          <Panel title="AI classification">
            <ClassificationPanel complaintId={c.id} ai={c.ai_classification} corrections={c.corrections}
                                 issueTypes={options.data?.issue_types ?? []} onCorrected={detail.reload} />
          </Panel>
          <Panel title="Location">
            <p className="px-4 pt-3 text-sm text-muted">
              {formatCoords(c.latitude, c.longitude)}; GPS accuracy {c.gps_accuracy != null ? `${Math.round(c.gps_accuracy)} m` : '-'}
            </p>
            <LocationMap latitude={c.latitude} longitude={c.longitude} band={c.priority.band} nearbyFacilities={c.nearby_facilities || c.priority?.nearby_facilities || []} />
          </Panel>
          <Panel title="Merged reports"><SplitPanel complaintId={c.id} reports={c.reports} onSplit={detail.reload} /></Panel>
        </div>
      </div>
    </>
  )
}
