import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Alert from "../components/Alert.jsx";
import { useAuth } from "../context/AuthContext.jsx";
import { useLanguage } from "../context/LanguageContext.jsx";
import { api } from "../lib/api.js";
import { firstName } from "../lib/roles.js";

// A plain card for something that will exist in a later module.
function ComingSoon({ title, text }) {
  const { t } = useLanguage();
  return (
    <div className="card">
      <h2 className="text-xl font-medium">{title}</h2>
      <p className="mt-1 text-muted">{text}</p>
      <p className="mt-3 inline-block rounded-full bg-accent-soft px-3 py-1 text-sm text-accent-dark">
        {t("home.comingSoon")}
      </p>
    </div>
  );
}

function CitizenHome() {
  const { t } = useLanguage();
  return (
    <div className="space-y-4">
      <div className="card">
        <h2 className="text-xl font-medium">{t("home.reportTitle")}</h2>
        <p className="mb-4 mt-1 text-muted">{t("home.reportText")}</p>
        <Link to="/report" className="btn btn-primary">
          {t("home.reportButton")}
        </Link>
      </div>
      <ComingSoon title={t("home.myTitle")} text={t("home.myText")} />
    </div>
  );
}

// Officer and admin screens are English only until Module 5.
function OfficerHome({ user }) {
  return (
    <div className="space-y-4">
      <p className="text-muted">
        Your department: <span className="font-medium text-ink">{user.department?.name ?? "Not assigned"}</span>
      </p>
      <div className="card">
        <h2 className="text-xl font-medium">Complaints for your department</h2>
        <p className="mt-1 text-muted">Review, prioritise and resolve reported problems.</p>
        <p className="mt-3 inline-block rounded-full bg-accent-soft px-3 py-1 text-sm text-accent-dark">Coming soon</p>
      </div>
    </div>
  );
}

function AdminHome() {
  const { t } = useLanguage();
  const [people, setPeople] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .users()
      .then(setPeople)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <section className="card" aria-labelledby="people-heading">
      <h2 id="people-heading" className="mb-4 text-xl font-medium">
        People ({people.length})
      </h2>
      <Alert>{error}</Alert>
      {loading && <p className="text-muted">…</p>}
      <ul className="divide-y divide-line">
        {people.map((person) => (
          <li key={person.id} className="py-3">
            <p className="font-medium">{person.full_name}</p>
            <p className="text-sm text-muted">
              {person.email} · {t(`role.${person.role}`)}
              {person.department ? ` · ${person.department.name}` : ""}
            </p>
          </li>
        ))}
      </ul>
    </section>
  );
}

export default function Home() {
  const { user } = useAuth();
  const { t } = useLanguage();

  return (
    <div>
      <h1 className="mb-1 text-3xl font-semibold">{t("home.hello", { name: firstName(user.full_name) })}</h1>
      <p className="mb-6 text-muted">{t("home.signedInAs", { role: t(`role.${user.role}`) })}</p>

      {user.role === "citizen" && <CitizenHome />}
      {user.role === "officer" && <OfficerHome user={user} />}
      {user.role === "admin" && <AdminHome />}
    </div>
  );
}
