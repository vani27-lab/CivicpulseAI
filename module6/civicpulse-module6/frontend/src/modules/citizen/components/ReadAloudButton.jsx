import { useI18n } from "../i18n/index.jsx";
import useSpeech from "../hooks/useSpeech";

/** Reads `text` in the selected language. If no voice exists, shows a note instead of failing. */
export default function ReadAloudButton({ text }) {
  const { lang, t } = useI18n();
  const { speak, stop, speaking, canSpeak, voicesLoaded } = useSpeech(lang);
  if (!text) return null;
  if (!canSpeak && voicesLoaded) return <p className="mt-1 text-xs text-slate-500">{t("voice.unavailable")}</p>;
  if (!canSpeak) return null;
  return <button type="button" onClick={() => (speaking ? stop() : speak(text))} aria-pressed={speaking}
    className="mt-1 rounded border border-slate-400 px-2 py-1 text-sm hover:bg-slate-100">
    {speaking ? t("btn.stop") : `🔊 ${t("btn.readAloud")}`}</button>;
}
