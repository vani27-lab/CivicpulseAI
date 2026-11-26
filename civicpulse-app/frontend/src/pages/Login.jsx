import { useState } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import Alert from "../components/Alert.jsx";
import Field from "../components/Field.jsx";
import { useAuth } from "../context/AuthContext.jsx";
import { useLanguage } from "../context/LanguageContext.jsx";

// For demos only. These accounts are created by the seed script (see README).
const SHOW_DEMO = import.meta.env.VITE_SHOW_DEMO_LOGINS !== "false";
const DEMO_PASSWORD = "Demo@1234";
const DEMO_ACCOUNTS = [
  { role: "citizen", email: "citizen@civicpulse.demo" },
  { role: "officer", email: "officer.roads@civicpulse.demo" },
  { role: "admin", email: "admin@civicpulse.demo" },
];

export default function Login() {
  const { user, login } = useAuth();
  const { t } = useLanguage();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  if (user) return <Navigate to="/" replace />;

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setBusy(true);
    try {
      await login(email.trim(), password);
      navigate(location.state?.from?.pathname || "/", { replace: true });
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-md">
      <h1 className="mb-2 text-3xl font-semibold">{t("login.title")}</h1>
      <p className="mb-6 text-muted">{t("login.subtitle")}</p>

      <form onSubmit={handleSubmit} className="card space-y-4">
        <Alert>{error}</Alert>
        <Field label={t("login.email")} type="email" value={email} onChange={setEmail} autoComplete="email" required />
        <Field
          label={t("login.password")}
          type="password"
          value={password}
          onChange={setPassword}
          autoComplete="current-password"
          required
        />
        <button type="submit" className="btn btn-primary w-full" disabled={busy}>
          {busy ? t("login.busy") : t("login.submit")}
        </button>
      </form>

      <p className="mt-6 text-center">
        {t("login.newHere")}{" "}
        <Link to="/register" className="font-medium text-accent-dark underline">
          {t("login.create")}
        </Link>
      </p>

      {SHOW_DEMO && (
        <section className="mt-8 rounded-xl bg-accent-soft p-5" aria-labelledby="demo-heading">
          <h2 id="demo-heading" className="font-medium">
            {t("login.demoTitle")}
          </h2>
          <p className="mb-3 text-sm text-muted">{t("login.demoHelp")}</p>
          <div className="flex flex-wrap gap-2">
            {DEMO_ACCOUNTS.map((account) => (
              <button
                key={account.email}
                type="button"
                className="btn btn-secondary"
                onClick={() => {
                  setEmail(account.email);
                  setPassword(DEMO_PASSWORD);
                  setError("");
                }}
              >
                {t(`role.${account.role}`)}
              </button>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
