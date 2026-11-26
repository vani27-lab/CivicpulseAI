import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Alert from "../components/Alert.jsx";
import { useAuth } from "../context/AuthContext.jsx";
import { useLanguage } from "../context/LanguageContext.jsx";
import { api } from "../lib/api.js";
import { firstName } from "../lib/roles.js";

function CitizenHome() {
  const { t } = useLanguage();
  return (
    <div className="space-y-4">
      <div className="card">
        <h2 className="text-xl font-medium">{t("home.reportTitle")}</h2>
        <p className="mb-4 mt-1 text-muted">{t("home.reportText")}</p>
        <div className="flex flex-wrap gap-3">
          <Link to="/report" className="btn btn-primary">
            {t("home.reportButton")}
          </Link>
          <Link to="/citizen/complaints" className="btn btn-secondary">
            Track My Complaints
          </Link>
        </div>
      </div>
      <div className="card">
        <h2 className="text-xl font-medium">My Submitted Complaints</h2>
        <p className="mt-1 text-muted">View live progress timeline, officer updates, and resolution status.</p>
        <Link to="/citizen/complaints" className="mt-3 inline-block font-medium text-accent hover:underline">
          Go to Citizen Tracking Portal &rarr;
        </Link>
      </div>
    </div>
  );
}

function OfficerHome({ user }) {
  return (
    <div className="space-y-4">
      <p className="text-muted">
        Your department: <span className="font-medium text-ink">{user.department?.name ?? "All Departments"}</span>
      </p>
      <div className="card">
        <h2 className="text-xl font-medium">Officer Dashboard</h2>
        <p className="mt-1 text-muted">
          Review complaints, view AI priority breakdown, manage status progression, inspect duplicate candidates, and view spatial heatmap.
        </p>
        <div className="mt-4 flex flex-wrap gap-3">
          <Link to="/officer" className="btn btn-primary">
            Open Officer Dashboard
          </Link>
          <Link to="/officer/map" className="btn btn-secondary">
            View Live Map & Heatmap
          </Link>
        </div>
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
    <div className="space-y-4">
      <div className="card">
        <h2 className="text-xl font-medium">Administrative Controls</h2>
        <p className="mt-1 text-muted">Access officer review queues, emergency overrides, and department stats.</p>
        <div className="mt-4 flex flex-wrap gap-3">
          <Link to="/officer" className="btn btn-primary">
            Officer Dashboard (Admin Mode)
          </Link>
          <Link to="/citizen/complaints" className="btn btn-secondary">
            Citizen Portal View
          </Link>
        </div>
      </div>

      <section className="card" aria-labelledby="people-heading">
        <h2 id="people-heading" className="mb-4 text-xl font-medium">
          People ({people.length})
        </h2>
        <Alert>{error}</Alert>
        {loading && <p className="text-muted">Loading...</p>}
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
    </div>
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
