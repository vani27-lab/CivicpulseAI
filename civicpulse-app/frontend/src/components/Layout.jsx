import { useEffect, useState } from "react";
import { Link, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import { useLanguage } from "../context/LanguageContext.jsx";
import { api } from "../lib/api.js";
import LanguageSwitcher from "./LanguageSwitcher.jsx";

function ServerStatus() {
  const { t } = useLanguage();
  const [state, setState] = useState("checking");

  useEffect(() => {
    api
      .health()
      .then((data) => setState(data.status === "ok" ? "ok" : "down"))
      .catch(() => setState("down"));
  }, []);

  const dot = { checking: "bg-line", ok: "bg-good", down: "bg-danger" }[state];

  return (
    <p className="flex items-center gap-2 text-sm text-muted">
      <span className={`inline-block h-2.5 w-2.5 rounded-full ${dot}`} aria-hidden="true" />
      {t(`server.${state}`)}
    </p>
  );
}

export default function Layout() {
  const { user, logout } = useAuth();
  const { t } = useLanguage();

  return (
    <div className="flex min-h-screen flex-col bg-slate-50 text-slate-900">
      <header className="border-b border-line bg-white shadow-sm">
        <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-3 px-4 py-3">
          <div className="flex items-center gap-6">
            <Link to="/" className="text-xl font-bold text-accent-dark tracking-tight">
              CivicPulse AI
            </Link>
            {user && (
              <nav className="flex items-center gap-4 text-sm font-medium">
                <Link to="/" className="text-muted hover:text-ink">
                  Home
                </Link>
                {user.role === "citizen" && (
                  <>
                    <Link to="/report" className="text-accent hover:underline">
                      + Report Problem
                    </Link>
                    <Link to="/citizen/complaints" className="text-muted hover:text-ink">
                      My Complaints
                    </Link>
                  </>
                )}
                {(user.role === "officer" || user.role === "admin") && (
                  <>
                    <Link to="/officer" className="text-accent hover:underline">
                      Officer Dashboard
                    </Link>
                    <Link to="/officer/map" className="text-muted hover:text-ink">
                      Heatmap
                    </Link>
                  </>
                )}
              </nav>
            )}
          </div>
          <div className="flex items-center gap-3">
            <LanguageSwitcher />
            {user ? (
              <div className="flex items-center gap-3">
                <div className="hidden text-right text-xs leading-tight md:block">
                  <span className="block font-medium text-ink">{user.full_name}</span>
                  <span className="block capitalize text-muted">{user.role}</span>
                </div>
                <button type="button" onClick={logout} className="btn btn-secondary text-xs py-1.5 px-3">
                  {t("nav.signOut")}
                </button>
              </div>
            ) : (
              <Link to="/login" className="btn btn-primary text-xs py-1.5 px-3">
                {t("nav.signIn")}
              </Link>
            )}
          </div>
        </div>
      </header>

      <main className="mx-auto w-full max-w-5xl flex-1 px-4 py-6">
        <Outlet />
      </main>

      <footer className="border-t border-line bg-white mt-auto">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
          <ServerStatus />
          <p className="text-xs text-muted">CivicPulse AI Unified MVP · Modules 1–6 Active</p>
        </div>
      </footer>
    </div>
  );
}
