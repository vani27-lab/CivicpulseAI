import { useState } from 'react'
import { officerApi } from '../api/officerApi'
import { EmptyState, ErrorState, LoadingState } from '../components/States'
import { OverviewMap } from '../components/OverviewMap'
import { useAsync } from '../hooks/useAsync'
import { PRIORITY_STYLES } from '../lib/labels'

export default function MapPage() {
  const [filters, setFilters] = useState({ department_id: '', issue_type: '', priority: '' })
  const [layers, setLayers] = useState({ markers: true, heat: true })
  const set = (key) => (e) => setFilters((f) => ({ ...f, [key]: e.target.value }))

  const options = useAsync((s) => officerApi.filterOptions(s), [])
  const points = useAsync((s) => officerApi.mapPoints({ ...filters, active_only: true }, s), [JSON.stringify(filters)])
  const heat = useAsync((s) => officerApi.heatmap(filters, s), [JSON.stringify(filters)])

  return (
    <>
      <h1 className="text-2xl font-bold">Complaint map</h1>
      <p className="text-sm text-muted">Open complaints only. Resolved and rejected complaints are hidden.</p>

      <section className="panel">
        <div className="grid gap-3 p-4 sm:grid-cols-3">
          <div>
            <label htmlFor="m-dept" className="label">Department</label>
            <select id="m-dept" className="field" value={filters.department_id} onChange={set('department_id')}>
              <option value="">All departments</option>
              {options.data?.departments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
            </select>
          </div>
          <div>
            <label htmlFor="m-type" className="label">Issue type</label>
            <select id="m-type" className="field" value={filters.issue_type} onChange={set('issue_type')}>
              <option value="">All issue types</option>
              {options.data?.issue_types.map((t) => <option key={t} value={t}>{t}</option>)}
            </select>
          </div>
          <div>
            <label htmlFor="m-pri" className="label">Priority</label>
            <select id="m-pri" className="field" value={filters.priority} onChange={set('priority')}>
              <option value="">All priorities</option>
              {['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map((p) => <option key={p} value={p}>{p}</option>)}
            </select>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-x-6 gap-y-2 border-t border-line px-4 py-3 text-sm">
          <label className="flex items-center gap-2">
            <input type="checkbox" checked={layers.markers} onChange={(e) => setLayers((l) => ({ ...l, markers: e.target.checked }))} />
            Complaint markers
          </label>
          <label className="flex items-center gap-2">
            <input type="checkbox" checked={layers.heat} onChange={(e) => setLayers((l) => ({ ...l, heat: e.target.checked }))} />
            Density heatmap
          </label>
          <ul className="ml-auto flex gap-4" aria-label="Marker colours">
            {Object.entries(PRIORITY_STYLES).map(([band, s]) => (
              <li key={band} className="flex items-center gap-1.5">
                <span aria-hidden="true" className="inline-block h-3 w-3 rounded-full" style={{ background: s.hex }} />{s.label}
              </li>
            ))}
          </ul>
        </div>

        {points.error ? <ErrorState error={points.error} onRetry={points.reload} />
          : points.loading && !points.data ? <LoadingState label="Loading map data..." />
          : points.data?.length === 0 ? <EmptyState title="No open complaints match these filters" />
          : <OverviewMap points={points.data ?? []} heat={heat.data?.points ?? []} showMarkers={layers.markers} showHeat={layers.heat} />}
        {heat.error && <ErrorState error={heat.error} onRetry={heat.reload} />}
      </section>
    </>
  )
}
