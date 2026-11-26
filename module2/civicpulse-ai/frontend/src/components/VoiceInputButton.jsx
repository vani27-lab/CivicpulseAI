import { useLanguage } from "../context/LanguageContext.jsx";
import { useSpeechRecognition } from "../hooks/useSpeechRecognition.js";

// "Speak" button. Finished sentences are passed to onText(text).
export default function VoiceInputButton({ onText }) {
  const { lang, t } = useLanguage();
  const { supported, listening, error, start, stop } = useSpeechRecognition({ lang, onText });

  if (!supported) {
    return <p className="text-sm text-muted">{t("report.voiceUnsupported")}</p>;
  }

  const errorText = { denied: "report.voiceDenied", nospeech: "report.voiceNoSpeech", error: "report.voiceError" }[error];

  return (
    <div className="space-y-2">
      <button
        type="button"
        className={`btn ${listening ? "bg-danger text-white hover:opacity-90" : "btn-secondary"}`}
        onClick={listening ? stop : start}
        aria-pressed={listening}
      >
        <span aria-hidden="true" className="mr-2">
          {listening ? "■" : "🎤"}
        </span>
        {listening ? t("report.voiceStop") : t("report.voiceStart")}
      </button>
      {listening && (
        <p role="status" className="text-sm text-muted">
          {t("report.voiceListening")}
        </p>
      )}
      {errorText && <p role="status" className="text-sm text-danger">{t(errorText)}</p>}
    </div>
  );
}
