// Standalone shell used only to run Module 5 on its own (npm run dev).
// In the integrated app, mount <OfficerRoutes /> inside the existing router instead.
import { Navigate, Route, Routes } from 'react-router-dom'
import { OfficerRoutes } from './officer'

export default function App() {
  return (
    <Routes>
      <Route path="/officer/*" element={<OfficerRoutes />} />
      <Route path="*" element={<Navigate to="/officer" replace />} />
    </Routes>
  )
}
