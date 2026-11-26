import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getComplaint, getHistory, getUpdates } from "../api";
import { useI18n } from "../i18n/index.jsx";
import { StatusBadge, PriorityTag, Spinner, ErrorBox, Empty } from "../components/ui";
import TrackingTimeline from "../components/TrackingTimeline";
import BeforeAfter from "../components/BeforeAfter";
import ReadAloudButton from "../components/ReadAloudButton";

export default function ComplaintTracking() {
  const { id } = useParams();
  const { t, lang, fmtDate } = useI18n();
  const [s, setS] = useState({ loading: true });
  const [updates, setUpdates] = useState([]);
  const load = useCallback(() => { setS({ loading: true });
    Promise.all([getComplaint(id), getHistory(id)])
      .then(([c, h]) => setS({ c, history: h.items }))
      .catch((e) => setS({ error: e.status === 404 ? "notFound" : "load" })); }, [id]);
  useEffect(load, [load]);
  useEffect(() => { getUpdates(id, lang).then((d) => setUpdates(d.items)).catch(() => setUpdates([])); }, [id, lang, s.c?.status]);

  if (s.loading) return <Spinner />;
  if (s.error) return <ErrorBox message={t(s.error === "notFound" ? "err.notFound" : "err.load")} onRetry={s.error === "load" ? load : undefined} />;
  const { c, history } = s;
  const statusLine = t("speak.status", { id: c.id.slice(0, 8), status: t(`status.${c.status}`) });
  return (
    <div className="space-y-8">
      <Link to="/citizen/complaints" className="text-sm underline">{t("btn.back")}</Link>
      <header>
        <h1 className="text-2xl font-bold">{t("tracking.title", { id: "#" + c.id.slice(0, 8) })}</h1>
        <p className="text-slate-600">{c.issue_type} · {fmtDate(c.created_at)}</p>
        <div className="mt-2 flex flex-wrap items-center gap-2"><StatusBadge status={c.status} /><PriorityTag band={c.priority_band} /></div>
        {c.citizen_urgency_reason && (c.priority_band === 'HIGH' || c.priority_band === 'CRITICAL' || c.is_emergency) && (
          <div className="mt-3 flex items-start gap-2.5 rounded-md border border-burgundy/30 bg-burgundy-soft p-3 text-sm text-burgundy-dark">
            <span className="font-bold uppercase tracking-wider text-xs bg-burgundy text-white px-1.5 py-0.5 rounded">Priority Notice</span>
            <p className="font-medium">{c.citizen_urgency_reason}</p>
          </div>
        )}
        <ReadAloudButton text={statusLine} />
      </header>

      <section><h2 className="mb-3 text-lg font-semibold">{t("tracking.progress")}</h2><TrackingTimeline history={history} /></section>

      <section><h2 className="mb-2 text-lg font-semibold">{t("tracking.updates")}</h2>
        {updates.length === 0 ? <Empty text={t("empty.updates")} /> : <ul className="space-y-3">{updates.map((u) => (
          <li key={u.id} className="rounded border border-slate-300 bg-white p-3">
            <p className="text-xs text-slate-500">{t(`status.${u.status}`)} · {fmtDate(u.created_at)}</p>
            {u.translated_comment ? (<>
              <p className="mt-1"><span className="text-xs text-slate-500">{t("tracking.translatedComment")}: </span>{u.translated_comment}</p>
              <p className="mt-1 text-sm text-slate-600"><span className="text-xs">{t("tracking.originalComment")}: </span>{u.comment}</p>
              <ReadAloudButton text={u.translated_comment} /></>) : (<><p className="mt-1">{u.comment}</p><ReadAloudButton text={u.comment} /></>)}
          </li>))}</ul>}</section>

      {c.status === "resolved" && <BeforeAfter before={c.before_photo_url} after={c.after_photo_url} />}

      <section><h2 className="mb-2 text-lg font-semibold">{t("tracking.yourDescription")}</h2>
        <p className="whitespace-pre-wrap">{c.original_description}</p>
        {c.translated_description && c.translated_description !== c.original_description &&
          <p className="mt-2 rounded bg-slate-50 p-3 text-sm"><span className="text-xs text-slate-500">{t("tracking.englishTranslation")}: </span>{c.translated_description}</p>}
      </section>
    </div>);
}
