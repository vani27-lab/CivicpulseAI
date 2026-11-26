import { useState } from "react";
import { useI18n } from "../i18n/index.jsx";
import { mediaUrl } from "../api";

const Pane = ({ label, src, empty }) => {
  const [failed, setFailed] = useState(false);
  const url = mediaUrl(src);

  return (
    <figure className="min-w-0">
      <figcaption className="mb-1 font-medium text-ink">{label}</figcaption>
      {url && !failed ? (
        <img
          src={url}
          alt={label}
          loading="lazy"
          className="aspect-[4/3] w-full rounded border border-line object-cover"
          onError={() => setFailed(true)}
        />
      ) : (
        <div className="grid aspect-[4/3] w-full place-items-center rounded bg-[#EDE8E0] border border-dashed border-line text-sm text-muted p-4 text-center">
          {failed ? "Photo file not found on disk" : empty}
        </div>
      )}
    </figure>
  );
};

/** Stacks on phones, side by side from sm: upward. */
export default function BeforeAfter({ before, after }) {
  const { t } = useI18n();
  return <section><h2 className="mb-2 text-lg font-semibold">{t("tracking.beforeAfter")}</h2>
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
      <Pane label={t("tracking.before")} src={before} empty={t("tracking.noPhoto")} />
      <Pane label={t("tracking.after")} src={after} empty={t("tracking.noPhoto")} /></div></section>;
}
