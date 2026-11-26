export function PriorityExplanation({ reasons }) {
  if (!reasons?.length) {
    return <p className="text-sm text-muted">The priority engine did not record an explanation for this complaint.</p>
  }
  return (
    <div>
      <p className="text-sm font-medium">Reasons</p>
      <ul className="mt-1 list-disc space-y-0.5 pl-5 text-sm">
        {reasons.map((reason, i) => <li key={`${i}-${reason}`}>{reason}</li>)}
      </ul>
    </div>
  )
}
