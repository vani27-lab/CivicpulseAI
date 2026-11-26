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
    <div className="flex min-h-screen flex-col">
      <header className="border-b border-line bg-white">
        <div className="mx-auto flex max-w-3xl flex-wrap items-center justify-between gap-3 px-4 py-3">
          <Link to="/" className="text-lg font-semibold text-accent-dark">
            CivicPulse AI
          </Link>
          <div className="flex items-center gap-3">
            <LanguageSwitcher />
            {user && (
              <>
                <p className="hidden text-right text-sm leading-tight md:block">
                  <span className="block font-medium">{user.full_name}</span>
                  <span className="block text-muted">{t(`role.${user.role}`)}</span>
                </p>
                <button type="button" onClick={logout} className="btn btn-secondary">
                  {t("nav.signOut")}
                </button>
              </>
            )}
          </div>
        </div>
      </header>

      <main className="mx-auto w-full max-w-3xl flex-1 px-4 py-8">
        <Outlet />
      </main>

      <footer className="border-t border-line bg-white">
        <div className="mx-auto max-w-3xl px-4 py-4">
          <ServerStatus />
        </div>
      </footer>
    </div>
  );
}
