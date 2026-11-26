import { lazy, Suspense } from 'react'
import { Route, Routes } from 'react-router-dom'
import { OfficerLoginPage } from './auth/OfficerLoginPage'
import { RequireOfficer } from './auth/RequireOfficer'
import { SessionProvider } from './auth/session'
import { LoadingState } from './components/States'
import { OfficerLayout } from './layout/OfficerLayout'

// Map pages pull in Leaflet, so they load on demand.
const DashboardPage = lazy(() => import('./pages/DashboardPage'))
const ComplaintDetailPage = lazy(() => import('./pages/ComplaintDetailPage'))
const MapPage = lazy(() => import('./pages/MapPage'))
const DuplicatesPage = lazy(() => import('./pages/DuplicatesPage'))

/** Mount with: <Route path="/officer/*" element={<OfficerRoutes />} /> */
export function OfficerRoutes() {
  return (
    <SessionProvider>
      <Suspense fallback={<LoadingState />}>
        <Routes>
          <Route path="login" element={<OfficerLoginPage />} />
          <Route element={<RequireOfficer><OfficerLayout /></RequireOfficer>}>
            <Route index element={<DashboardPage />} />
            <Route path="complaints/:id" element={<ComplaintDetailPage />} />
            <Route path="map" element={<MapPage />} />
            <Route path="duplicates" element={<DuplicatesPage />} />
          </Route>
        </Routes>
      </Suspense>
    </SessionProvider>
  )
}
