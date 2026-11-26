import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import Alert from "../components/Alert.jsx";
import Field from "../components/Field.jsx";
import { useAuth } from "../context/AuthContext.jsx";
import { useLanguage } from "../context/LanguageContext.jsx";

export default function Register() {
  const { user, register } = useAuth();
  const { lang, t } = useLanguage();
  const navigate = useNavigate();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  if (user) return <Navigate to="/" replace />;

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    if (password.length < 8) {
      setError(t("register.passwordShort"));
      return;
    }
    setBusy(true);
    try {
      // The language chosen on screen becomes the account's preferred language.
      await register({ full_name: fullName.trim(), email: email.trim(), password, preferred_language: lang });
      navigate("/", { replace: true });
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-md">
      <h1 className="mb-2 text-3xl font-semibold">{t("register.title")}</h1>
      <p className="mb-6 text-muted">{t("register.subtitle")}</p>

      <form onSubmit={handleSubmit} className="card space-y-4">
        <Alert>{error}</Alert>
        <Field label={t("register.fullName")} value={fullName} onChange={setFullName} autoComplete="name" required />
        <Field label={t("login.email")} type="email" value={email} onChange={setEmail} autoComplete="email" required />
        <Field
          label={t("login.password")}
          type="password"
          value={password}
          onChange={setPassword}
          autoComplete="new-password"
          hint={t("register.passwordHint")}
          required
        />
        <button type="submit" className="btn btn-primary w-full" disabled={busy}>
          {busy ? t("register.busy") : t("register.submit")}
        </button>
      </form>

      <p className="mt-6 text-center">
        {t("register.haveAccount")}{" "}
        <Link to="/login" className="font-medium text-accent-dark underline">
          {t("login.submit")}
        </Link>
      </p>
    </div>
  );
}
