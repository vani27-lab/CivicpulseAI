import { useCallback, useEffect, useRef, useState } from "react";

// The browser's built-in speech-to-text. It works in Google Chrome and Edge (and Safari
// to some degree). Firefox does not support it, so we always keep typing available.
// Chrome sends the audio to Google's servers to turn it into text.
const SpeechRecognition =
  typeof window !== "undefined" ? window.SpeechRecognition || window.webkitSpeechRecognition : undefined;

const LOCALES = { en: "en-IN", hi: "hi-IN" };

// lang: "en" | "hi".  onText(text): called with each finished sentence.
export function useSpeechRecognition({ lang, onText }) {
  const [listening, setListening] = useState(false);
  const [error, setError] = useState(""); // "", "denied", "nospeech" or "error"
  const recognitionRef = useRef(null);
  const onTextRef = useRef(onText);
  onTextRef.current = onText;

  const supported = Boolean(SpeechRecognition);

  const start = useCallback(() => {
    if (!SpeechRecognition) return;
    setError("");
    const recognition = new SpeechRecognition();
    recognition.lang = LOCALES[lang] || "en-IN";
    recognition.continuous = true;
    recognition.interimResults = false;

    recognition.onresult = (event) => {
      let text = "";
      for (let i = event.resultIndex; i < event.results.length; i += 1) {
        if (event.results[i].isFinal) text += event.results[i][0].transcript;
      }
      if (text.trim()) onTextRef.current(text.trim());
    };
    recognition.onerror = (event) => {
      if (event.error === "not-allowed" || event.error === "service-not-allowed") setError("denied");
      else if (event.error === "no-speech") setError("nospeech");
      else if (event.error !== "aborted") setError("error");
    };
    recognition.onend = () => {
      setListening(false);
      recognitionRef.current = null;
    };

    recognitionRef.current = recognition;
    recognition.start();
    setListening(true);
  }, [lang]);

  const stop = useCallback(() => recognitionRef.current?.stop(), []);

  // Stop listening when the page is closed.
  useEffect(() => () => recognitionRef.current?.abort(), []);

  return { supported, listening, error, start, stop };
}
