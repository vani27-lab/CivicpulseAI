import { useEffect } from "react";
import { NavLink, Outlet, Navigate, useNavigate } from "react-router-dom";
import { useI18n } from "./i18n/index.jsx";
import { LanguageSwitcher } from "./components/ui";
import NotificationBell from "./components/NotificationBell";
import { hasToken } from "./api";

const LOGIN = import.meta.env.VITE_LOGIN_PATH || "/login";

/** Client-side guard for UX only; the API enforces JWT + ownership. */
export default function CitizenShell() {
  const { t } = useI18n();
  const nav = useNavigate();
  useEffect(() => { const f = () => nav(LOGIN); window.addEventListener("auth:expired", f); return () => window.removeEventListener("auth:expired", f); }, [nav]);
  if (!hasToken()) return <Navigate to={LOGIN} replace />;
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="border-b border-slate-300 bg-white">
        <div className="mx-auto flex max-w-3xl items-center justify-between gap-3 px-4 py-3">
          <div className="flex items-center gap-4">
            <NavLink to="/" className="text-sm font-medium text-slate-600 hover:text-slate-900">&larr; Home</NavLink>
            <NavLink to="/citizen/complaints" className="font-bold">{t("app.name")}</NavLink>
          </div>
          <div className="flex items-center gap-3"><LanguageSwitcher /><NotificationBell /></div></div></header>
      <main className="mx-auto max-w-3xl px-4 py-6"><Outlet /></main>
    </div>);
}
