import { useCallback, useEffect, useState } from "react";
import { LANGUAGES } from "../i18n/index.jsx";

/** Browser text-to-speech. speak() returns false (never throws) if no voice exists. */
export default function useSpeech(lang) {
  const supported = typeof window !== "undefined" && "speechSynthesis" in window;
  const [voices, setVoices] = useState([]);
  const [speaking, setSpeaking] = useState(false);
  useEffect(() => {
    if (!supported) return;
    const load = () => setVoices(window.speechSynthesis.getVoices());
    load(); window.speechSynthesis.addEventListener("voiceschanged", load);
    return () => { window.speechSynthesis.removeEventListener("voiceschanged", load); window.speechSynthesis.cancel(); };
  }, [supported]);
  const prefix = LANGUAGES[lang]?.voice || lang;
  const voice = voices.find((v) => v.lang.toLowerCase().startsWith(prefix)) || null;
  const canSpeak = supported && !!voice;
  const speak = useCallback((text) => {
    if (!canSpeak || !text) return false;
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.voice = voice; u.lang = voice.lang;
    u.onstart = () => setSpeaking(true); u.onend = u.onerror = () => setSpeaking(false);
    window.speechSynthesis.speak(u); return true;
  }, [canSpeak, voice]);
  const stop = useCallback(() => { if (supported) window.speechSynthesis.cancel(); setSpeaking(false); }, [supported]);
  return { speak, stop, speaking, canSpeak, voicesLoaded: voices.length > 0 };
}
