import { Navigate, useLocation } from 'react-router-dom'
import { isOfficerRole, useSession } from './session'

export function RequireOfficer({ children }) {
  const { status, user } = useSession()
  const location = useLocation()

  if (status === 'loading') {
    return <p role="status" className="p-8 text-muted">Checking your session...</p>
  }
  if (status !== 'authenticated') {
    return <Navigate to="/officer/login" replace state={{ from: location.pathname + location.search }} />
  }
  if (!isOfficerRole(user?.role)) {
    return (
      <main className="mx-auto max-w-md p-8">
        <h1 className="text-xl font-semibold">Officer access only</h1>
        <p className="mt-2 text-muted">
          Your account is signed in as a citizen, so it cannot open the officer dashboard. Use the citizen
          app to track your complaints.
        </p>
      </main>
    )
  }
  return children
}
