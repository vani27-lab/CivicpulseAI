import { buildTimeline } from "../timeline";
import { useI18n } from "../i18n/index.jsx";

export default function TrackingTimeline({ history }) {
  const { t, fmtDate } = useI18n();
  const steps = buildTimeline(history);
  return (
    <ol className="relative ml-3 border-l-2 border-slate-300">
      {steps.map((s) => (
        <li key={s.status} className="mb-6 ml-6" aria-current={s.current ? "step" : undefined}>
          <span aria-hidden className={`absolute -left-[9px] mt-1 h-4 w-4 rounded-full border-2 ${
            s.reached ? "border-emerald-700 bg-emerald-600" : "border-slate-300 bg-white"} ${s.current ? "ring-4 ring-emerald-200" : ""}`} />
          <p className={`font-semibold ${s.reached ? "text-slate-900" : "text-slate-500"}`}>{t(`status.${s.status}`)}</p>
          {s.reached ? (<>
            <p className="text-sm text-slate-600">{fmtDate(s.entry.created_at)}</p>
            {s.entry.comment && <p className="mt-1 text-sm text-slate-800">{s.entry.comment}</p>}
          </>) : <p className="text-sm text-slate-500">{t("tracking.notYet")}</p>}
        </li>))}
    </ol>);
}
