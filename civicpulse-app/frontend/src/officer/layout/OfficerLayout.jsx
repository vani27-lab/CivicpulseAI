import { NavLink, Outlet } from 'react-router-dom'
import { useSession } from '../auth/session'

const link = ({ isActive }) =>
  `rounded-md px-3 py-1.5 text-sm font-medium ${isActive ? 'bg-white text-civic-dark' : 'text-white/90 hover:bg-civic-dark'}`

export function OfficerLayout() {
  const { user, signOut } = useSession()
  return (
    <div className="min-h-screen">
      <a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:left-2 focus:top-2 focus:z-50 focus:rounded focus:bg-white focus:px-3 focus:py-2">
        Skip to content
      </a>
      <header className="bg-civic text-white">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3 px-4 py-3">
          <div className="flex flex-wrap items-center gap-4">
            <p className="text-lg font-bold">CivicPulse <span className="font-medium text-white/80">Officer</span></p>
            <nav aria-label="Officer" className="flex gap-1">
              <NavLink to="/" className={link}>Home</NavLink>
              <NavLink to="/officer" end className={link}>Complaints</NavLink>
              <NavLink to="/officer/map" className={link}>Map</NavLink>
              <NavLink to="/officer/duplicates" className={link}>Duplicates</NavLink>
            </nav>
          </div>
          <div className="flex items-center gap-3 text-sm">
            <span>{user?.name || user?.email} <span className="text-white/70">({user?.role})</span></span>
            <button type="button" onClick={signOut} className="rounded-md border border-white/50 px-3 py-1.5 font-medium hover:bg-civic-dark">
              Sign out
            </button>
          </div>
        </div>
      </header>
      <main id="main" className="mx-auto max-w-7xl space-y-4 px-4 py-6">
        <Outlet />
      </main>
    </div>
  )
}
