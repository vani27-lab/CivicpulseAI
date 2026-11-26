import { Link } from "react-router-dom";
import { useLanguage } from "../context/LanguageContext.jsx";

export default function NotFound() {
  const { t } = useLanguage();
  return (
    <div className="mx-auto max-w-md text-center">
      <h1 className="mb-2 text-3xl font-semibold">{t("notFound.title")}</h1>
      <p className="mb-6 text-muted">{t("notFound.text")}</p>
      <Link to="/" className="btn btn-primary">
        {t("notFound.home")}
      </Link>
    </div>
  );
}
