import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getMine, mediaUrl } from "../api";
import { useI18n } from "../i18n/index.jsx";
import { StatusBadge, PriorityTag, Spinner, ErrorBox, Empty } from "../components/ui";

export default function MyComplaints() {
  const { t, fmtDate } = useI18n();
  const [state, setState] = useState({ loading: true });
  const load = useCallback(() => { setState({ loading: true });
    getMine().then((d) => setState({ data: d })).catch(() => setState({ error: true })); }, []);
  useEffect(load, [load]);
  if (state.loading) return <Spinner />;
  if (state.error) return <ErrorBox message={t("err.load")} onRetry={load} />;
  const { stats, items } = state.data;
  return (
    <div>
      <h1 className="mb-4 text-2xl font-bold">{t("list.title")}</h1>
      <dl className="mb-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
        {["total", "pending", "in_progress", "resolved"].map((k) => (
          <div key={k} className="rounded border border-slate-300 bg-white p-3"><dt className="text-sm text-slate-600">{t(`stats.${k}`)}</dt>
            <dd className="text-2xl font-semibold">{stats[k]}</dd></div>))}
      </dl>
      {items.length === 0 ? <Empty text={t("empty.complaints")} /> :
        <ul className="space-y-3">{items.map((c) => (
          <li key={c.id} className="flex gap-3 rounded border border-slate-300 bg-white p-3">
            {c.thumbnail ? <img src={mediaUrl(c.thumbnail)} alt="" loading="lazy" className="h-20 w-20 shrink-0 rounded object-cover" />
              : <div className="h-20 w-20 shrink-0 rounded bg-slate-100" />}
            <div className="min-w-0 flex-1">
              <p className="truncate font-semibold">{c.issue_type} <span className="font-normal text-slate-500">#{c.id.slice(0, 8)}</span></p>
              <p className="text-sm text-slate-600">{t("list.submittedOn", { date: fmtDate(c.created_at) })}</p>
              <div className="mt-1 flex flex-wrap items-center gap-2"><StatusBadge status={c.status} /><PriorityTag band={c.priority_band} /></div>
              <Link to={c.id} className="mt-2 inline-block text-sm font-medium text-sky-800 underline">{t("btn.view")}</Link>
            </div></li>))}</ul>}
    </div>);
}
