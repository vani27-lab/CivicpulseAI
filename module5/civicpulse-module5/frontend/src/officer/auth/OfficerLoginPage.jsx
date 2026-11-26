import { useState } from 'react'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import { isOfficerRole, useSession } from './session'

export function OfficerLoginPage() {
  const { status, user, signIn } = useSession()
  const navigate = useNavigate()
  const location = useLocation()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)

  if (status === 'authenticated' && isOfficerRole(user?.role)) {
    return <Navigate to={location.state?.from || '/officer'} replace />
  }

  const submit = async (event) => {
    event.preventDefault()
    setBusy(true)
    setError(null)
    try {
      await signIn(email.trim(), password)
      navigate(location.state?.from || '/officer', { replace: true })
    } catch (err) {
      setError(err.message || 'Sign-in failed. Try again.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-sm flex-col justify-center px-4">
      <h1 className="text-2xl font-bold text-civic-dark">CivicPulse officer sign-in</h1>
      <p className="mt-1 text-sm text-muted">Use your government-issued officer account.</p>
      <form onSubmit={submit} className="panel mt-6 space-y-4 p-5" noValidate>
        <div>
          <label htmlFor="email" className="label">Email</label>
          <input id="email" type="email" autoComplete="username" required className="field"
                 value={email} onChange={(e) => setEmail(e.target.value)} />
        </div>
        <div>
          <label htmlFor="password" className="label">Password</label>
          <input id="password" type="password" autoComplete="current-password" required className="field"
                 value={password} onChange={(e) => setPassword(e.target.value)} />
        </div>
        {error && <p role="alert" className="rounded-md bg-high-tint px-3 py-2 text-sm text-high-text">{error}</p>}
        <button type="submit" className="btn-primary w-full" disabled={busy || !email || !password}>
          {busy ? 'Signing in...' : 'Sign in'}
        </button>
      </form>
    </main>
  )
}
