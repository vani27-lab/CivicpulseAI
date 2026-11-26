import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { STRINGS } from "../i18n/strings.js";

const STORAGE_KEY = "civicpulse_lang";
const LanguageContext = createContext(null);

function loadSavedLanguage() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    return saved === "hi" || saved === "en" ? saved : "en";
  } catch {
    return "en";
  }
}

export function LanguageProvider({ children }) {
  const [lang, setLangState] = useState(loadSavedLanguage);

  // Tells the browser (and screen readers) which language the page is in.
  useEffect(() => {
    document.documentElement.lang = lang;
  }, [lang]);

  const setLang = useCallback((next) => {
    try {
      localStorage.setItem(STORAGE_KEY, next);
    } catch {
      // saving the choice is optional
    }
    setLangState(next);
  }, []);

  // t("home.hello", { name: "Asha" })  ->  "Hello, Asha"
  const t = useCallback(
    (key, values) => {
      let text = STRINGS[lang]?.[key] ?? STRINGS.en[key] ?? key;
      if (values) {
        for (const [name, value] of Object.entries(values)) text = text.replaceAll(`{${name}}`, String(value));
      }
      return text;
    },
    [lang]
  );

  const value = useMemo(() => ({ lang, setLang, t }), [lang, setLang, t]);
  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

export function useLanguage() {
  const context = useContext(LanguageContext);
  if (!context) throw new Error("useLanguage must be used inside <LanguageProvider>");
  return context;
}
