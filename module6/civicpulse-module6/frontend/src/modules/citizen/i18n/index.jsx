import { createContext, useContext, useState, useCallback, useMemo } from "react";
import en from "./en";
import hi from "./hi";

// Add a language: create xx.js, register it here. Missing keys fall back to English.
export const LANGUAGES = { en: { label: "English", dict: en, locale: "en-IN", voice: "en" },
                           hi: { label: "हिन्दी", dict: hi, locale: "hi-IN", voice: "hi" } };
const Ctx = createContext(null);
const KEY = "civicpulse.lang";

export function LanguageProvider({ children }) {
  const [lang, setLangState] = useState(() => (LANGUAGES[localStorage.getItem(KEY)] ? localStorage.getItem(KEY) : "en"));
  const setLang = useCallback((l) => { if (LANGUAGES[l]) { localStorage.setItem(KEY, l); setLangState(l); document.documentElement.lang = l; } }, []);
  const t = useCallback((k, vars = {}) => {
    const s = LANGUAGES[lang].dict[k] ?? en[k] ?? k;
    return s.replace(/\{(\w+)\}/g, (_, v) => vars[v] ?? "");
  }, [lang]);
  const fmtDate = useCallback((d) => new Date(d).toLocaleString(LANGUAGES[lang].locale, { dateStyle: "medium", timeStyle: "short" }), [lang]);
  const value = useMemo(() => ({ lang, setLang, t, fmtDate }), [lang, setLang, t, fmtDate]);
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}
export const useI18n = () => useContext(Ctx);
