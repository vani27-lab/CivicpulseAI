import { useEffect, useState } from "react";
import { Link, NavLink, Outlet } from "react-router-dom";
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
    <p className="flex items-center gap-2 text-xs font-medium text-muted">
      <span className={`inline-block h-2 w-2 rounded-full ${dot}`} aria-hidden="true" />
      <span>System: {t(`server.${state}`)}</span>
    </p>
  );
}

export default function Layout() {
  const { user, logout } = useAuth();
  const { t } = useLanguage();

  const navLinkClass = ({ isActive }) =>
    `text-sm font-medium transition-colors px-2.5 py-1 rounded-md ${
      isActive
        ? "text-burgundy bg-burgundy-soft font-semibold"
        : "text-muted hover:text-ink hover:bg-black/5"
    }`;

  return (
    <div className="flex min-h-screen flex-col bg-page text-ink">
      {/* Top editorial brand bar */}
      <header className="border-b border-line bg-white/95 backdrop-blur-sm sticky top-0 z-30 shadow-editorial">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-4 py-3 sm:px-6">
          <div className="flex items-center gap-8">
            <Link to="/" className="flex items-center gap-2 group">
              <span className="font-serif text-2xl font-bold tracking-tight text-ink group-hover:text-burgundy transition-colors">
                CivicPulse
              </span>
              <span className="rounded bg-burgundy px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wider text-white">
                AI
              </span>
            </Link>

            {user && (
              <nav className="hidden md:flex items-center gap-1.5 border-l border-line pl-6">
                <NavLink to="/" end className={navLinkClass}>
                  Home
                </NavLink>
                {user.role === "citizen" && (
                  <>
                    <NavLink to="/report" className={navLinkClass}>
                      Report Problem
                    </NavLink>
                    <NavLink to="/citizen/complaints" className={navLinkClass}>
                      My Complaints
                    </NavLink>
                  </>
                )}
                {(user.role === "officer" || user.role === "admin") && (
                  <>
                    <NavLink to="/officer" end className={navLinkClass}>
                      Officer Dashboard
                    </NavLink>
                    <NavLink to="/officer/map" className={navLinkClass}>
                      Map & Heatmap
                    </NavLink>
                    <NavLink to="/officer/duplicates" className={navLinkClass}>
                      Duplicate Review
                    </NavLink>
                  </>
                )}
              </nav>
            )}
          </div>

          <div className="flex items-center gap-3">
            <LanguageSwitcher />

            {user ? (
              <div className="flex items-center gap-3 border-l border-line pl-3">
                <div className="hidden text-right text-xs leading-snug sm:block">
                  <span className="block font-semibold text-ink">{user.full_name}</span>
                  <span className="block capitalize text-muted">{user.role}</span>
                </div>
                <button
                  type="button"
                  onClick={logout}
                  className="btn btn-secondary text-xs min-h-[2.25rem] px-3.5 py-1"
                >
                  {t("nav.signOut")}
                </button>
              </div>
            ) : (
              <Link to="/login" className="btn btn-primary text-xs min-h-[2.25rem] px-4 py-1">
                {t("nav.signIn")}
              </Link>
            )}
          </div>
        </div>
      </header>

      {/* Main workspace */}
      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8 sm:px-6">
        <Outlet />
      </main>

      {/* Modern Industrial Editorial footer */}
      <footer className="border-t border-line bg-white/60 py-4 mt-auto">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-4 sm:px-6">
          <ServerStatus />
          <p className="text-xs text-muted tracking-wide font-medium">
            CivicPulse AI Municipal Infrastructure Platform · Modern Industrial Editorial
          </p>
        </div>
      </footer>
    </div>
  );
}
