"""Lightweight language detection (Hindi/English first, regional scripts supported).

Detection is script-based and dependency-free. Romanised Hindi ("Hinglish") looks
like English to a script check, so the model-reported language may refine an
"en" result (see reconcile_language).
"""
import re
from typing import Optional

UNDETERMINED = "und"

# (start, end, language code) Unicode blocks.
_SCRIPT_RANGES = [
    (0x0900, 0x097F, "hi"),  # Devanagari (Hindi; Marathi/Nepali share the script)
    (0x0980, 0x09FF, "bn"),  # Bengali
    (0x0A00, 0x0A7F, "pa"),  # Gurmukhi (Punjabi)
    (0x0A80, 0x0AFF, "gu"),  # Gujarati
    (0x0B00, 0x0B7F, "or"),  # Odia
    (0x0B80, 0x0BFF, "ta"),  # Tamil
    (0x0C00, 0x0C7F, "te"),  # Telugu
    (0x0C80, 0x0CFF, "kn"),  # Kannada
    (0x0D00, 0x0D7F, "ml"),  # Malayalam
    (0x0600, 0x06FF, "ur"),  # Arabic script (Urdu)
]

_NAME_TO_CODE = {
    "hindi": "hi", "english": "en", "bengali": "bn", "punjabi": "pa", "gujarati": "gu",
    "odia": "or", "oriya": "or", "tamil": "ta", "telugu": "te", "kannada": "kn",
    "malayalam": "ml", "urdu": "ur", "marathi": "mr",
}

_CODE_RE = re.compile(r"^[a-z]{2,3}$")


def normalize_language_code(value: Optional[str]) -> Optional[str]:
    """Return a lowercase 2-3 letter code, or None if the value is unusable."""
    if not value or not isinstance(value, str):
        return None
    v = value.strip().lower()
    if v in _NAME_TO_CODE:
        return _NAME_TO_CODE[v]
    v = v.split("-")[0].split("_")[0]
    return v if _CODE_RE.match(v) else None


def detect_language(text: str, hint: Optional[str] = None) -> str:
    """Detect the language of `text`. An explicit valid `hint` always wins."""
    hinted = normalize_language_code(hint)
    if hinted:
        return hinted
    counts: dict = {}
    for ch in text or "":
        cp = ord(ch)
        for lo, hi, code in _SCRIPT_RANGES:
            if lo <= cp <= hi:
                counts[code] = counts.get(code, 0) + 1
                break
        else:
            if ch.isalpha() and ch.isascii():
                counts["en"] = counts.get("en", 0) + 1
    if not counts:
        return UNDETERMINED
    return max(counts, key=counts.get)


def reconcile_language(heuristic: str, model_language: Optional[str], text: str, hint: Optional[str] = None) -> str:
    """Let the model correct an 'en' guess (e.g. romanised Hindi), unless the caller gave a hint."""
    if normalize_language_code(hint):
        return heuristic
    reported = normalize_language_code(model_language)
    if heuristic == "en" and reported and reported != "en" and (text or "").strip():
        return reported
    return heuristic
