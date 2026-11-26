import { useI18n, LANGUAGES } from "../i18n/index.jsx";

const TONE = { submitted: "bg-slate-100 text-slate-800", assigned: "bg-sky-100 text-sky-900",
  in_progress: "bg-amber-100 text-amber-900", resolved: "bg-emerald-100 text-emerald-900", rejected: "bg-rose-100 text-rose-900" };
const BAND = { CRITICAL: "border-red-700 bg-red-100 text-red-900 font-bold", HIGH: "border-red-600 text-red-800", MEDIUM: "border-orange-600 text-orange-800", LOW: "border-green-700 text-green-800" };

export const StatusBadge = ({ status }) => { const { t } = useI18n();
  return <span className={`inline-block rounded px-2 py-0.5 text-sm font-medium ${TONE[status] || TONE.submitted}`}>{t(`status.${status}`)}</span>; };
export const PriorityTag = ({ band }) => { const { t } = useI18n();
  return band ? <span className={`inline-block rounded border px-2 py-0.5 text-sm ${BAND[band] || ""}`}>{t(`priority.${band}`)}</span> : null; };
export const Spinner = () => { const { t } = useI18n(); return <p role="status" className="py-10 text-center text-slate-600">{t("loading")}</p>; };
export const ErrorBox = ({ message, onRetry }) => { const { t } = useI18n();
  return <div role="alert" className="rounded border border-rose-300 bg-rose-50 p-4 text-rose-900">
    <p>{message}</p>{onRetry && <button onClick={onRetry} className="mt-2 underline">{t("btn.retry")}</button>}</div>; };
export const Empty = ({ text }) => <p className="rounded border border-dashed border-slate-300 p-6 text-center text-slate-600">{text}</p>;

export function LanguageSwitcher() { const { lang, setLang, t } = useI18n();
  return <label className="flex items-center gap-2 text-sm"><span className="sr-only">{t("lang.label")}</span>
    <select value={lang} onChange={(e) => setLang(e.target.value)} className="rounded border border-slate-300 bg-white px-2 py-1">
      {Object.entries(LANGUAGES).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}</select></label>; }
