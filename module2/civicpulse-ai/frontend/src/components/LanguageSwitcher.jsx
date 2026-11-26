import { useLanguage } from "../context/LanguageContext.jsx";

const LANGUAGES = [
  { code: "en", label: "English" },
  { code: "hi", label: "हिन्दी" },
];

export default function LanguageSwitcher() {
  const { lang, setLang, t } = useLanguage();
  return (
    <div role="group" aria-label={t("nav.language")} className="flex overflow-hidden rounded-lg border border-line">
      {LANGUAGES.map((item) => (
        <button
          key={item.code}
          type="button"
          lang={item.code}
          aria-pressed={lang === item.code}
          onClick={() => setLang(item.code)}
          className={`min-h-[2.75rem] px-3 text-sm font-medium ${
            lang === item.code ? "bg-accent text-white" : "bg-white text-ink hover:bg-page"
          }`}
        >
          {item.label}
        </button>
      ))}
    </div>
  );
}
