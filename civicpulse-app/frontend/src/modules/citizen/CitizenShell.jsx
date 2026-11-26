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
  useEffect(() => {
    const f = () => nav(LOGIN);
    window.addEventListener("auth:expired", f);
    return () => window.removeEventListener("auth:expired", f);
  }, [nav]);

  if (!hasToken()) return <Navigate to={LOGIN} replace />;

  return (
    <div className="min-h-screen bg-page text-ink flex flex-col">
      <header className="border-b border-line bg-white shadow-editorial sticky top-0 z-30">
        <div className="mx-auto flex max-w-4xl items-center justify-between gap-4 px-4 py-3 sm:px-6">
          <div className="flex items-center gap-6">
            <NavLink
              to="/"
              className="text-xs font-semibold text-muted hover:text-burgundy transition-colors flex items-center gap-1"
            >
              &larr; Main Home
            </NavLink>
            <div className="h-4 w-px bg-line" />
            <NavLink to="/citizen/complaints" className="flex items-center gap-2">
              <span className="font-serif text-xl font-bold tracking-tight text-ink">
                {t("app.name")}
              </span>
              <span className="rounded bg-burgundy-soft px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wider text-burgundy">
                Citizen Portal
              </span>
            </NavLink>
          </div>
          <div className="flex items-center gap-4">
            <LanguageSwitcher />
            <NotificationBell />
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-4xl w-full px-4 py-6 sm:px-6 flex-1">
        <Outlet />
      </main>
      <footer className="border-t border-line bg-white/40 py-3 mt-auto">
        <div className="mx-auto max-w-4xl px-4 sm:px-6 text-xs text-muted flex justify-between items-center">
          <span>CivicPulse Citizen Resolution Tracker</span>
          <span className="text-[11px] font-medium">Verified Live Status</span>
        </div>
      </footer>
    </div>
  );
}
