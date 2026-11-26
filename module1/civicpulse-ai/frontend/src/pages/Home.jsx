import { useEffect, useState } from "react";
import Alert from "../components/Alert.jsx";
import { useAuth } from "../context/AuthContext.jsx";
import { api } from "../lib/api.js";
import { ROLE_LABELS, firstName } from "../lib/roles.js";

// A big, plain card for something that will exist in a later module.
function ComingSoon({ title, text }) {
  return (
    <div className="card">
      <h2 className="text-xl font-medium">{title}</h2>
      <p className="mt-1 text-muted">{text}</p>
      <p className="mt-3 inline-block rounded-full bg-accent-soft px-3 py-1 text-sm text-accent-dark">
        Coming soon
      </p>
    </div>
  );
}

function CitizenHome() {
  return (
    <div className="space-y-4">
      <ComingSoon title="Report a problem" text="Add a photo, share the location and describe what is wrong." />
      <ComingSoon title="My complaints" text="See how your reports are progressing." />
    </div>
  );
}

function OfficerHome({ user }) {
  return (
    <div className="space-y-4">
      <p className="text-muted">
        Your department: <span className="font-medium text-ink">{user.department?.name ?? "Not assigned"}</span>
      </p>
      <ComingSoon title="Complaints for your department" text="Review, prioritise and resolve reported problems." />
    </div>
  );
}

function AdminHome() {
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
      {loading && <p className="text-muted">Loading…</p>}
      <ul className="divide-y divide-line">
        {people.map((person) => (
          <li key={person.id} className="py-3">
            <p className="font-medium">{person.full_name}</p>
            <p className="text-sm text-muted">
              {person.email} · {ROLE_LABELS[person.role]}
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

  return (
    <div>
      <h1 className="mb-1 text-3xl font-semibold">Hello, {firstName(user.full_name)}</h1>
      <p className="mb-6 text-muted">You are signed in as {ROLE_LABELS[user.role].toLowerCase()}.</p>

      {user.role === "citizen" && <CitizenHome />}
      {user.role === "officer" && <OfficerHome user={user} />}
      {user.role === "admin" && <AdminHome />}
    </div>
  );
}
