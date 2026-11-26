"""Helpers for displaying Module 4's priority output. Module 5 never recomputes a
score; it only turns the stored explanation into a list the UI can render."""
import json


def parse_reasons(raw) -> list[str]:
    """``complaints.priority_reason`` may be a JSON list, a JSON object with a
    ``reasons`` key, or plain text separated by newlines / semicolons / bullets."""
    if raw is None:
        return []
    if isinstance(raw, (list, tuple)):
        return [str(x).strip() for x in raw if str(x).strip()]
    if isinstance(raw, dict):
        return parse_reasons(raw.get("reasons"))
    text = str(raw).strip()
    if not text:
        return []
    if text[0] in "[{":
        try:
            return parse_reasons(json.loads(text))
        except (ValueError, TypeError):
            pass
    parts = []
    for line in text.replace(";", "\n").splitlines():
        cleaned = line.strip().lstrip("-*\u2022").strip()
        if cleaned:
            parts.append(cleaned)
    return parts
