import { Navigate } from "react-router-dom";
import { LanguageProvider } from "./i18n/index.jsx";
import CitizenShell from "./CitizenShell";
import MyComplaints from "./pages/MyComplaints";
import ComplaintTracking from "./pages/ComplaintTracking";

/** Add to Module 1's router: const routes = [...existing, citizenRoutes] */
export const citizenRoutes = {
  path: "/citizen",
  element: <LanguageProvider><CitizenShell /></LanguageProvider>,
  children: [
    { index: true, element: <Navigate to="complaints" replace /> },
    { path: "complaints", element: <MyComplaints /> },
    { path: "complaints/:id", element: <ComplaintTracking /> },
  ],
};
