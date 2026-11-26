"""Vision AI client abstraction. Swap providers by implementing VisionClient."""
import base64
import logging
from typing import Optional, Protocol

import httpx

from .config import Settings
from .exceptions import VisionAPIError

logger = logging.getLogger(__name__)


class VisionClient(Protocol):
    def analyze(self, image_bytes: bytes, media_type: str, prompt: str) -> str:
        """Return the model's raw text reply. Raise VisionAPIError on any API failure."""
        ...


def detect_media_type(image_bytes: bytes) -> Optional[str]:
    """Identify the image type from magic bytes (never trust client headers)."""
    if image_bytes.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if image_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if image_bytes[:4] == b"RIFF" and image_bytes[8:12] == b"WEBP":
        return "image/webp"
    if image_bytes[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif"
    return None


class AnthropicVisionClient:
    """Default implementation using the Anthropic Messages API over HTTPS."""

    def __init__(self, settings: Settings, http_client: Optional[httpx.Client] = None):
        self._s = settings
        self._http = http_client

    def analyze(self, image_bytes: bytes, media_type: str, prompt: str) -> str:
        if not self._s.vision_api_key:
            raise VisionAPIError("AI_VISION_API_KEY is not configured")
        payload = {
            "model": self._s.vision_model,
            "max_tokens": self._s.vision_max_tokens,
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "image", "source": {
                        "type": "base64", "media_type": media_type,
                        "data": base64.b64encode(image_bytes).decode("ascii")}},
                    {"type": "text", "text": prompt},
                ],
            }],
        }
        headers = {
            "x-api-key": self._s.vision_api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        try:
            if self._http is not None:
                resp = self._http.post(self._s.vision_api_url, json=payload, headers=headers,
                                       timeout=self._s.vision_timeout_seconds)
            else:
                with httpx.Client(timeout=self._s.vision_timeout_seconds) as http:
                    resp = http.post(self._s.vision_api_url, json=payload, headers=headers)
            resp.raise_for_status()
            body = resp.json()
        except (httpx.HTTPError, ValueError) as exc:
            logger.warning("Vision API call failed: %s", type(exc).__name__)
            raise VisionAPIError(f"Vision API call failed: {type(exc).__name__}") from exc

        blocks = body.get("content") if isinstance(body, dict) else None
        if not isinstance(blocks, list):
            raise VisionAPIError("Unexpected Vision API response shape")
        return "".join(b.get("text", "") for b in blocks if isinstance(b, dict) and b.get("type") == "text")


def build_default_client(settings: Settings) -> VisionClient:
    if settings.vision_provider.lower() == "anthropic":
        return AnthropicVisionClient(settings)
    raise VisionAPIError(f"Unsupported vision provider: {settings.vision_provider}")
