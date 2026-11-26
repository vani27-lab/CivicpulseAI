import { Route, Routes, Navigate } from "react-router-dom";
import Layout from "./components/Layout.jsx";
import ProtectedRoute from "./components/ProtectedRoute.jsx";
import Home from "./pages/Home.jsx";
import Login from "./pages/Login.jsx";
import NotFound from "./pages/NotFound.jsx";
import Register from "./pages/Register.jsx";
import ReportProblem from "./pages/ReportProblem.jsx";
import { OfficerRoutes } from "./officer/OfficerRoutes.jsx";
import CitizenShell from "./modules/citizen/CitizenShell.jsx";
import MyComplaints from "./modules/citizen/pages/MyComplaints.jsx";
import ComplaintTracking from "./modules/citizen/pages/ComplaintTracking.jsx";
import { LanguageProvider as CitizenLanguageProvider } from "./modules/citizen/i18n/index.jsx";

export default function App() {
  return (
    <Routes>
      {/* Officer Dashboard Routes */}
      <Route path="/officer/*" element={<OfficerRoutes />} />

      {/* Citizen Tracking Routes */}
      <Route
        path="/citizen/*"
        element={
          <CitizenLanguageProvider>
            <CitizenShell />
          </CitizenLanguageProvider>
        }
      >
        <Route index element={<Navigate to="complaints" replace />} />
        <Route path="complaints" element={<MyComplaints />} />
        <Route path="complaints/:id" element={<ComplaintTracking />} />
      </Route>

      {/* Core Foundation & Report Routes */}
      <Route element={<Layout />}>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Home />
            </ProtectedRoute>
          }
        />
        <Route
          path="/report"
          element={
            <ProtectedRoute roles={["citizen"]}>
              <ReportProblem />
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  );
}
