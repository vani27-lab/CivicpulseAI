"""Strict validation of the raw AI response. Dependency-free on purpose."""
import json
import re
from dataclasses import dataclass
from typing import Optional

from .constants import SEVERITY_MAX, SEVERITY_MIN, VALID_ISSUE_TYPES
from .exceptions import MalformedAIResponse

_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE)
_MAX_REASON_CHARS = 200


@dataclass(frozen=True)
class ParsedAIResult:
    issue_type: str
    severity: int
    confidence: float
    reason: str
    detected_language: Optional[str] = None
    translated_text: Optional[str] = None


def _extract_json_object(text: str) -> str:
    if not isinstance(text, str) or not text.strip():
        raise MalformedAIResponse("Empty AI response")
    cleaned = _FENCE_RE.sub("", text.strip()).strip()
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start == -1 or end <= start:
        raise MalformedAIResponse("No JSON object found in AI response")
    return cleaned[start : end + 1]


def validate_fields(data: dict) -> ParsedAIResult:
    """Validate an already-decoded dict (also used for saved demo entries)."""
    if not isinstance(data, dict):
        raise MalformedAIResponse("AI response is not a JSON object")

    issue_type = data.get("issue_type")
    if not isinstance(issue_type, str) or issue_type.strip().lower() not in VALID_ISSUE_TYPES:
        raise MalformedAIResponse(f"Invalid issue_type: {issue_type!r}")

    severity = data.get("severity")
    if isinstance(severity, bool) or not isinstance(severity, int) or not (SEVERITY_MIN <= severity <= SEVERITY_MAX):
        raise MalformedAIResponse(f"Invalid severity: {severity!r}")

    confidence = data.get("confidence")
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)) or not (0.0 <= confidence <= 1.0):
        raise MalformedAIResponse(f"Invalid confidence: {confidence!r}")

    reason = data.get("reason")
    if not isinstance(reason, str) or not reason.strip():
        raise MalformedAIResponse("Missing reason")
    reason = " ".join(reason.split())[:_MAX_REASON_CHARS]

    language = data.get("detected_language")
    if language is not None and not isinstance(language, str):
        raise MalformedAIResponse("Invalid detected_language")

    translated = data.get("translated_text")
    if translated is not None and not isinstance(translated, str):
        raise MalformedAIResponse("Invalid translated_text")

    return ParsedAIResult(
        issue_type=issue_type.strip().lower(),
        severity=severity,
        confidence=float(confidence),
        reason=reason,
        detected_language=language,
        translated_text=translated.strip() if isinstance(translated, str) else None,
    )


def parse_ai_response(text: str) -> ParsedAIResult:
    """Parse and strictly validate model output. Raises MalformedAIResponse."""
    raw = _extract_json_object(text)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise MalformedAIResponse(f"Invalid JSON: {exc}") from exc
    return validate_fields(data)
