import { NavLink, Outlet } from 'react-router-dom'
import { useSession } from '../auth/session'

const link = ({ isActive }) =>
  `rounded-md px-3 py-1.5 text-sm font-medium transition-all ${
    isActive
      ? 'bg-white text-burgundy shadow-sm font-semibold'
      : 'text-white/85 hover:text-white hover:bg-black/15'
  }`

export function OfficerLayout() {
  const { user, signOut } = useSession()
  return (
    <div className="min-h-screen bg-page text-ink flex flex-col">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:left-2 focus:top-2 focus:z-50 focus:rounded focus:bg-white focus:px-3 focus:py-2 focus:shadow"
      >
        Skip to content
      </a>
      <header className="bg-burgundy text-white shadow-editorial border-b border-burgundy-dark sticky top-0 z-30">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-4 py-3 sm:px-6">
          <div className="flex flex-wrap items-center gap-6">
            <div className="flex items-center gap-2">
              <span className="font-serif text-xl font-bold tracking-tight text-white">CivicPulse</span>
              <span className="rounded bg-white/20 px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wider text-white">
                Officer
              </span>
            </div>
            <nav aria-label="Officer navigation" className="flex gap-1.5">
              <NavLink to="/" className={link}>Main Home</NavLink>
              <NavLink to="/officer" end className={link}>Complaints Triage</NavLink>
              <NavLink to="/officer/map" className={link}>Heatmap & GIS</NavLink>
              <NavLink to="/officer/duplicates" className={link}>Duplicate Review</NavLink>
            </nav>
          </div>
          <div className="flex items-center gap-3 text-xs sm:text-sm">
            <span className="font-medium text-white/95">
              {user?.name || user?.email}{' '}
              <span className="text-white/70 uppercase text-[11px] font-bold ml-1">({user?.role})</span>
            </span>
            <button
              type="button"
              onClick={signOut}
              className="rounded border border-white/30 px-2.5 py-1 text-xs font-semibold hover:bg-white hover:text-burgundy transition-colors"
            >
              Sign out
            </button>
          </div>
        </div>
      </header>
      <main id="main" className="mx-auto max-w-7xl w-full space-y-6 px-4 py-6 sm:px-6 flex-1">
        <Outlet />
      </main>
      <footer className="border-t border-line bg-white/40 py-3 mt-auto">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 text-xs text-muted flex justify-between items-center">
          <span>CivicPulse AI Officer Control Center</span>
          <span className="text-[11px] uppercase tracking-wider font-semibold">Priority & Triage Active</span>
        </div>
      </footer>
    </div>
  )
}
