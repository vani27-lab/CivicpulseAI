"""Optional comment translation. Never raises; returns None on any failure.
TRANSLATION_PROVIDER=libretranslate + LIBRETRANSLATE_URL enables it. Default: off."""
import os
import httpx
from sqlalchemy import text

def _provider_translate(txt, lang):
    if os.getenv("TRANSLATION_PROVIDER", "none") != "libretranslate":
        return None
    r = httpx.post(os.environ["LIBRETRANSLATE_URL"].rstrip("/") + "/translate",
                   json={"q": txt, "source": "en", "target": lang, "format": "text"}, timeout=3.0)
    r.raise_for_status()
    return r.json().get("translatedText")

def translate_cached(db, history_id, txt, lang, provider=_provider_translate):
    if not txt or lang == "en":
        return None
    try:
        row = db.execute(text("SELECT text FROM comment_translations WHERE status_history_id=:h AND lang=:l"),
                         {"h": history_id, "l": lang}).first()
        if row:
            return row[0]
        out = provider(txt, lang)
        if out:
            db.execute(text("INSERT INTO comment_translations(status_history_id,lang,text) VALUES(:h,:l,:t) "
                            "ON CONFLICT DO NOTHING"), {"h": history_id, "l": lang, "t": out})
            db.commit()
        return out
    except Exception:
        try: db.rollback()
        except Exception: pass
        return None
