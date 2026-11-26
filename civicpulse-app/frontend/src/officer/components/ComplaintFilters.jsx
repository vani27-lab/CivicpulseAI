const EMPTY = { q: '', department_id: '', issue_type: '', priority: '', status: '', date_from: '', date_to: '' }

export function ComplaintFilters({ value, options, onChange }) {
  const set = (key) => (e) => onChange({ ...value, [key]: e.target.value })
  const active = Object.keys(EMPTY).some((k) => value[k])

  return (
    <form className="grid grid-cols-1 gap-3 p-4 sm:grid-cols-2 lg:grid-cols-4" role="search" onSubmit={(e) => e.preventDefault()}>
      <div className="sm:col-span-2 lg:col-span-4">
        <label htmlFor="f-q" className="label">Search</label>
        <input id="f-q" type="search" className="field" placeholder="Complaint ID, issue, description, department"
               value={value.q} onChange={set('q')} />
      </div>
      <div>
        <label htmlFor="f-dept" className="label">Department</label>
        <select id="f-dept" className="field" value={value.department_id} onChange={set('department_id')}>
          <option value="">All departments</option>
          {options.departments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
        </select>
      </div>
      <div>
        <label htmlFor="f-type" className="label">Issue type</label>
        <select id="f-type" className="field" value={value.issue_type} onChange={set('issue_type')}>
          <option value="">All issue types</option>
          {options.issue_types.map((t) => <option key={t} value={t}>{t}</option>)}
        </select>
      </div>
      <div>
        <label htmlFor="f-priority" className="label">Priority</label>
        <select id="f-priority" className="field" value={value.priority} onChange={set('priority')}>
          <option value="">All priorities</option>
          {options.priorities.map((p) => <option key={p} value={p}>{p}</option>)}
        </select>
      </div>
      <div>
        <label htmlFor="f-status" className="label">Status</label>
        <select id="f-status" className="field" value={value.status} onChange={set('status')}>
          <option value="">All statuses</option>
          {options.statuses.map((s) => <option key={s.value} value={s.value}>{s.label}</option>)}
        </select>
      </div>
      <div>
        <label htmlFor="f-from" className="label">Submitted from</label>
        <input id="f-from" type="date" className="field" value={value.date_from} onChange={set('date_from')} />
      </div>
      <div>
        <label htmlFor="f-to" className="label">Submitted to</label>
        <input id="f-to" type="date" className="field" value={value.date_to} onChange={set('date_to')} />
      </div>
      <div className="flex items-end">
        <button type="button" className="btn-secondary" disabled={!active} onClick={() => onChange({ ...EMPTY })}>
          Clear filters
        </button>
      </div>
    </form>
  )
}

ComplaintFilters.EMPTY = EMPTY
