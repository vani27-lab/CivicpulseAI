import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Alert from "../components/Alert.jsx";
import LocationPicker from "../components/LocationPicker.jsx";
import VoiceInputButton from "../components/VoiceInputButton.jsx";
import { useLanguage } from "../context/LanguageContext.jsx";
import { api } from "../lib/api.js";

const MAX_PHOTO_MB = 10; // keep in step with MAX_UPLOAD_MB in the backend
const PHOTO_TYPES = ["image/jpeg", "image/png", "image/webp"];

export default function ReportProblem() {
  const { lang, t } = useLanguage();
  const [photo, setPhoto] = useState(null);
  const [photoUrl, setPhotoUrl] = useState("");
  const [location, setLocation] = useState(null);
  const [description, setDescription] = useState("");
  const [usedVoice, setUsedVoice] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState(null);

  // Make a preview of the chosen photo, and free its memory when it changes.
  useEffect(() => {
    if (!photo) {
      setPhotoUrl("");
      return undefined;
    }
    const url = URL.createObjectURL(photo);
    setPhotoUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [photo]);

  function handlePhoto(event) {
    const file = event.target.files?.[0];
    if (!file) return;
    setError("");
    if (!PHOTO_TYPES.includes(file.type)) {
      setError(t("report.photoBadType"));
      return;
    }
    if (file.size > MAX_PHOTO_MB * 1024 * 1024) {
      setError(t("report.photoTooBig", { mb: MAX_PHOTO_MB }));
      return;
    }
    setPhoto(file);
  }

  function handleVoiceText(text) {
    setUsedVoice(true);
    setDescription((previous) => (previous ? `${previous} ${text}` : text));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    if (!photo) return setError(t("report.needPhoto"));
    if (!location) return setError(t("report.needLocation"));
    if (description.trim().length < 3) return setError(t("report.needDescription"));

    const form = new FormData();
    form.append("image", photo);
    form.append("latitude", location.latitude);
    form.append("longitude", location.longitude);
    if (location.accuracy != null) form.append("location_accuracy_m", location.accuracy);
    form.append("location_source", location.source);
    form.append("description", description.trim());
    form.append("description_language", lang);
    form.append("used_voice_input", usedVoice);

    setBusy(true);
    try {
      setResult(await api.submitReport(form));
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  function startAnother() {
    setPhoto(null);
    setLocation(null);
    setDescription("");
    setUsedVoice(false);
    setError("");
    setResult(null);
  }

  if (result) {
    return (
      <div className="card text-center" role="status">
        <h1 className="mb-2 text-3xl font-semibold">{t("report.doneTitle")}</h1>
        <p className="mb-6 text-muted">{t("report.doneText", { id: result.complaint_id })}</p>
        <div className="flex flex-col justify-center gap-3 sm:flex-row">
          <button type="button" className="btn btn-primary" onClick={startAnother}>
            {t("report.doneAnother")}
          </button>
          <Link to="/" className="btn btn-secondary">
            {t("report.doneHome")}
          </Link>
        </div>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6" noValidate>
      <div>
        <h1 className="mb-1 text-3xl font-semibold">{t("report.title")}</h1>
        <p className="text-muted">{t("report.intro")}</p>
      </div>

      <section className="card space-y-3" aria-labelledby="photo-heading">
        <div>
          <h2 id="photo-heading" className="text-xl font-medium">{t("report.photoTitle")}</h2>
          <p className="text-muted">{t("report.photoHelp")}</p>
        </div>
        {photoUrl && (
          <img src={photoUrl} alt={t("report.photoAlt")} className="max-h-72 w-full rounded-lg border border-line object-contain" />
        )}
        <label className="btn btn-secondary cursor-pointer focus-within:ring-2 focus-within:ring-accent">
          {photo ? t("report.photoChange") : t("report.photoChoose")}
          <input type="file" accept="image/jpeg,image/png,image/webp" onChange={handlePhoto} className="sr-only" />
        </label>
      </section>

      <section className="card space-y-3" aria-labelledby="location-heading">
        <div>
          <h2 id="location-heading" className="text-xl font-medium">{t("report.locTitle")}</h2>
          <p className="text-muted">{t("report.locHelp")}</p>
        </div>
        <LocationPicker value={location} onChange={setLocation} />
      </section>

      <section className="card space-y-3" aria-labelledby="description-heading">
        <div>
          <h2 id="description-heading" className="text-xl font-medium">{t("report.descTitle")}</h2>
          <p className="text-muted">{t("report.descHelp")}</p>
        </div>
        <label htmlFor="description" className="block font-medium">{t("report.descLabel")}</label>
        <textarea
          id="description"
          rows={4}
          maxLength={2000}
          value={description}
          onChange={(event) => setDescription(event.target.value)}
          placeholder={t("report.descPlaceholder")}
          className="input py-3"
        />
        <VoiceInputButton onText={handleVoiceText} />
      </section>

      <Alert>{error}</Alert>
      <button type="submit" className="btn btn-primary w-full" disabled={busy}>
        {busy ? t("report.sending") : t("report.submit")}
      </button>
    </form>
  );
}
