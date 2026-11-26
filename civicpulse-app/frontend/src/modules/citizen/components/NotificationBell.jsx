import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getNotifications, markRead, markAllRead } from "../api";
import { useI18n } from "../i18n/index.jsx";

export default function NotificationBell() {
  const { t, fmtDate } = useI18n();
  const [data, setData] = useState({ unread: 0, items: [] });
  const [open, setOpen] = useState(false);
  const load = useCallback(() => getNotifications().then(setData).catch(() => {}), []); // silent: bell must not break the page
  useEffect(() => { load(); const i = setInterval(load, 60000); return () => clearInterval(i); }, [load]);
  const msg = (n) => { const k = `notif.${n.status}`; const s = t(k); return s !== k ? s : t("notif.default"); };
  return (
    <div className="relative">
      <button onClick={() => setOpen(!open)} aria-expanded={open} aria-label={t("nav.notifications")} className="relative rounded p-2 hover:bg-slate-100">
        🔔{data.unread > 0 && <span className="absolute -right-0.5 -top-0.5 rounded-full bg-red-600 px-1.5 text-xs text-white">{data.unread}</span>}</button>
      {open && <div className="absolute right-0 z-20 mt-1 w-80 max-w-[90vw] rounded border border-slate-300 bg-white shadow-lg">
        <div className="flex items-center justify-between border-b p-2"><b>{t("nav.notifications")}</b>
          {data.unread > 0 && <button className="text-sm underline" onClick={() => markAllRead().then(load)}>{t("btn.markAllRead")}</button>}</div>
        {data.items.length === 0 ? <p className="p-4 text-sm text-slate-600">{t("empty.notifications")}</p> :
          <ul className="max-h-80 overflow-auto">{data.items.map((n) => (
            <li key={n.id} className={n.is_read ? "" : "bg-sky-50"}>
              <Link to={`/citizen/complaints/${n.complaint_id}`} onClick={() => { setOpen(false); markRead(n.id).then(load); }} className="block border-b p-3 text-sm hover:bg-slate-50">
                <p>{msg(n)}</p><p className="text-xs text-slate-500">{fmtDate(n.created_at)}</p></Link></li>))}</ul>}
      </div>}
    </div>);
}
