export function LoadingState({ label = 'Loading...' }) {
  return <p role="status" className="px-4 py-10 text-center text-sm text-muted">{label}</p>
}

export function ErrorState({ error, onRetry }) {
  return (
    <div role="alert" className="m-4 rounded-md border border-high-rail/40 bg-high-tint px-4 py-3 text-sm text-high-text">
      <p className="font-semibold">Something went wrong</p>
      <p className="mt-1">{error?.message || 'The data could not be loaded.'}</p>
      {onRetry && <button type="button" onClick={onRetry} className="btn-secondary mt-3">Try again</button>}
    </div>
  )
}

export function EmptyState({ title, children }) {
  return (
    <div className="px-4 py-10 text-center">
      <p className="font-semibold">{title}</p>
      {children && <p className="mx-auto mt-1 max-w-md text-sm text-muted">{children}</p>}
    </div>
  )
}
