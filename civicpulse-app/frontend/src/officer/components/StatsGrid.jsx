const CARDS = [
  { key: 'total', label: 'Total complaints' },
  { key: 'pending', label: 'Pending' },
  { key: 'in_progress', label: 'In progress' },
  { key: 'resolved', label: 'Resolved' },
  { key: 'high_priority', label: 'High priority, open' },
]

export function StatsGrid({ stats }) {
  return (
    <dl className="grid grid-cols-2 gap-3 md:grid-cols-5" aria-label="Complaint summary">
      {CARDS.map(({ key, label }) => (
        <div key={key} className={`panel px-4 py-3 ${key === 'high_priority' ? 'border-l-4 border-l-high-rail' : ''}`}>
          <dt className="text-sm text-muted">{label}</dt>
          <dd className="mt-1 text-2xl font-bold tabular-nums">{stats[key]}</dd>
        </div>
      ))}
    </dl>
  )
}
