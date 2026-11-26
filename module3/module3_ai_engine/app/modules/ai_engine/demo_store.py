"""Saved demo results, keyed by SHA-256 image fingerprint (API-failure fallback)."""
import json
import logging
import threading
from pathlib import Path
from typing import Optional

from .exceptions import MalformedAIResponse
from .parser import ParsedAIResult, validate_fields

logger = logging.getLogger(__name__)


class DemoResultStore:
    def __init__(self, path: str):
        self._path = Path(path)
        self._entries: Optional[dict] = None
        self._lock = threading.Lock()

    def _load(self) -> dict:
        if self._entries is not None:
            return self._entries
        with self._lock:
            if self._entries is None:
                entries: dict = {}
                try:
                    raw = json.loads(self._path.read_text(encoding="utf-8"))
                    if isinstance(raw, dict):
                        entries = {k.lower(): v for k, v in raw.items()
                                   if isinstance(k, str) and not k.startswith("_")}
                except FileNotFoundError:
                    logger.info("No demo results file at %s", self._path)
                except (OSError, ValueError) as exc:
                    logger.warning("Could not read demo results: %s", exc)
                self._entries = entries
        return self._entries

    def lookup(self, fingerprint: str) -> Optional[ParsedAIResult]:
        entry = self._load().get(fingerprint.lower())
        if entry is None:
            return None
        try:
            return validate_fields(entry)
        except MalformedAIResponse as exc:
            logger.warning("Ignoring invalid demo entry %s...: %s", fingerprint[:8], exc)
            return None

    def reload(self) -> None:
        with self._lock:
            self._entries = None
