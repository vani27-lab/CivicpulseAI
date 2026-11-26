"""Environment-driven configuration. No secrets are hardcoded."""
import os
from dataclasses import dataclass


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    vision_provider: str = "anthropic"
    vision_api_key: str = ""
    vision_api_url: str = "https://api.anthropic.com/v1/messages"
    vision_model: str = "claude-sonnet-4-6"
    vision_timeout_seconds: float = 30.0
    vision_max_tokens: int = 600
    max_image_bytes: int = 5 * 1024 * 1024
    max_description_chars: int = 2000
    confidence_threshold: float = 0.70
    demo_fallback_enabled: bool = True
    demo_results_path: str = "data/saved_demo_results.json"

    @classmethod
    def from_env(cls) -> "Settings":
        d = cls()
        return cls(
            vision_provider=os.getenv("AI_VISION_PROVIDER", d.vision_provider),
            vision_api_key=os.getenv("AI_VISION_API_KEY", d.vision_api_key),
            vision_api_url=os.getenv("AI_VISION_API_URL", d.vision_api_url),
            vision_model=os.getenv("AI_VISION_MODEL", d.vision_model),
            vision_timeout_seconds=float(os.getenv("AI_VISION_TIMEOUT_SECONDS", d.vision_timeout_seconds)),
            vision_max_tokens=int(os.getenv("AI_VISION_MAX_TOKENS", d.vision_max_tokens)),
            max_image_bytes=int(os.getenv("AI_MAX_IMAGE_BYTES", d.max_image_bytes)),
            max_description_chars=int(os.getenv("AI_MAX_DESCRIPTION_CHARS", d.max_description_chars)),
            confidence_threshold=float(os.getenv("AI_CONFIDENCE_THRESHOLD", d.confidence_threshold)),
            demo_fallback_enabled=_env_bool("AI_DEMO_FALLBACK_ENABLED", d.demo_fallback_enabled),
            demo_results_path=os.getenv("AI_DEMO_RESULTS_PATH", d.demo_results_path),
        )
