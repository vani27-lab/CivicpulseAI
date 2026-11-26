"""classify_complaint(): the reusable service Module 4 calls directly.

Guarantee: classify_complaint() never raises. Every failure path degrades to a
saved demo result or an Unclassified result with needs_review=True, so complaint
submission is never blocked.
"""
import logging
from typing import Optional

from .config import Settings
from .constants import (DEMO_REASON_PREFIX, IssueType, SOURCE_DEMO, SOURCE_FALLBACK, SOURCE_LIVE)
from .demo_store import DemoResultStore
from .exceptions import MalformedAIResponse, VisionAPIError
from .fingerprint import sha256_hex
from .language import UNDETERMINED, detect_language, reconcile_language
from .parser import ParsedAIResult, parse_ai_response
from .prompts import build_prompt
from .schemas import ClassificationResult
from .vision_client import VisionClient, build_default_client, detect_media_type

logger = logging.getLogger(__name__)


class ComplaintClassifier:
    def __init__(self, settings: Optional[Settings] = None, client: Optional[VisionClient] = None,
                 demo_store: Optional[DemoResultStore] = None):
        self.settings = settings or Settings.from_env()
        self._client = client
        self._demo = demo_store or DemoResultStore(self.settings.demo_results_path)

    @property
    def client(self) -> VisionClient:
        if self._client is None:
            self._client = build_default_client(self.settings)
        return self._client

    # ---- public API -------------------------------------------------------
    def classify_complaint(self, image_bytes: bytes, description: str, language: Optional[str] = None
                           ) -> ClassificationResult:
        text = (description or "").strip()[: self.settings.max_description_chars]
        lang = detect_language(text, language)
        try:
            return self._classify(image_bytes or b"", text, lang, language)
        except Exception:  # noqa: BLE001 - last-resort guard; must never block submission
            logger.exception("Unexpected error in classify_complaint; returning Unclassified")
            return self._unclassified("Classification failed unexpectedly; manual review required", text, lang)

    # ---- internals --------------------------------------------------------
    def _classify(self, image: bytes, text: str, lang: str, hint: Optional[str]) -> ClassificationResult:
        if not image:
            return self._unclassified("No image provided", text, lang)
        if len(image) > self.settings.max_image_bytes:
            return self._unclassified("Image too large for AI analysis", text, lang)
        media_type = detect_media_type(image)
        if media_type is None:
            return self._unclassified("Unsupported image format", text, lang)

        try:
            parsed = self._call_with_retry(image, media_type, text)
        except VisionAPIError:
            return self._from_demo(image, text, lang)
        if parsed is None:
            return self._unclassified("AI response could not be validated; manual review required", text, lang)

        lang = reconcile_language(lang, parsed.detected_language, text, hint)
        return self._build(parsed, text, lang, SOURCE_LIVE)

    def _call_with_retry(self, image: bytes, media_type: str, text: str) -> Optional[ParsedAIResult]:
        """One attempt + one retry on malformed output. API errors propagate."""
        for attempt in (0, 1):
            raw = self.client.analyze(image, media_type, build_prompt(text, strict_retry=attempt == 1))
            try:
                return parse_ai_response(raw)
            except MalformedAIResponse as exc:
                logger.warning("Malformed AI response (attempt %d): %s", attempt + 1, exc)
        return None

    def _from_demo(self, image: bytes, text: str, lang: str) -> ClassificationResult:
        if self.settings.demo_fallback_enabled:
            entry = self._demo.lookup(sha256_hex(image))
            if entry is not None:
                demo = ParsedAIResult(entry.issue_type, entry.severity, entry.confidence,
                                      DEMO_REASON_PREFIX + entry.reason, None, entry.translated_text)
                return self._build(demo, text, lang, SOURCE_DEMO)
        return self._unclassified("AI service unavailable; manual review required", text, lang)

    def _build(self, p: ParsedAIResult, text: str, lang: str, source: str) -> ClassificationResult:
        if lang in ("en", UNDETERMINED):
            translated = text
        else:
            translated = p.translated_text or ""  # empty => translation unavailable
        needs_review = (p.confidence < self.settings.confidence_threshold
                        or p.issue_type == IssueType.UNCLASSIFIED.value)
        return ClassificationResult(
            issue_type=p.issue_type, severity=p.severity, confidence=p.confidence, reason=p.reason,
            detected_language=lang, original_text=text, translated_text=translated,
            needs_review=needs_review, source=source)

    def _unclassified(self, reason: str, text: str, lang: str) -> ClassificationResult:
        translated = text if lang in ("en", UNDETERMINED) else ""
        return ClassificationResult(
            issue_type=IssueType.UNCLASSIFIED.value, severity=1, confidence=0.0, reason=reason,
            detected_language=lang, original_text=text, translated_text=translated,
            needs_review=True, source=SOURCE_FALLBACK)


# ---- module-level convenience (the agreed Module 3 service interface) ----
_default: Optional[ComplaintClassifier] = None


def get_default_classifier() -> ComplaintClassifier:
    global _default
    if _default is None:
        _default = ComplaintClassifier()
    return _default


def set_default_classifier(classifier: Optional[ComplaintClassifier]) -> None:
    """Dependency-injection hook (tests, or the main app's own wiring)."""
    global _default
    _default = classifier


def classify_complaint(image_bytes: bytes, description: str, language: Optional[str] = None
                       ) -> ClassificationResult:
    return get_default_classifier().classify_complaint(image_bytes, description, language)
