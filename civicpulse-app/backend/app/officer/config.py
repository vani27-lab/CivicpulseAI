"""Module 5 settings, read from environment variables (see backend/.env.example).

Read lazily on each call so tests can monkeypatch the environment."""
import os
from dataclasses import dataclass


def _bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _csv(name: str, default: str) -> tuple[str, ...]:
    return tuple(p.strip().lower() for p in os.getenv(name, default).split(",") if p.strip())


@dataclass(frozen=True)
class Settings:
    # Roles (must match the values Module 1 stores in users.role)
    officer_roles: tuple[str, ...]
    admin_role: str
    # Status storage convention in complaints.status / status_history.*_status
    status_style: str  # "snake" -> in_progress ; "title" -> In Progress
    enable_rejected: bool
    # After-photo storage
    upload_dir: str
    media_base_url: str
    max_upload_bytes: int
    # Optional integrations with Module 4
    duplicate_service_module: str
    reroute_hook: str
    # Route mounting (turn off when Module 1/4 already expose an equivalent route)
    mount_heatmap: bool
    mount_duplicate_routes: bool


def get_settings() -> Settings:
    return Settings(
        officer_roles=_csv("M5_OFFICER_ROLES", "officer,admin"),
        admin_role=os.getenv("M5_ADMIN_ROLE", "admin").strip().lower(),
        status_style=os.getenv("M5_STATUS_STYLE", "snake").strip().lower(),
        enable_rejected=_bool("M5_ENABLE_REJECTED", True),
        upload_dir=os.getenv("M5_UPLOAD_DIR", "uploads"),
        media_base_url=os.getenv("M5_MEDIA_BASE_URL", "/media").rstrip("/"),
        max_upload_bytes=int(os.getenv("M5_MAX_UPLOAD_MB", "8")) * 1024 * 1024,
        duplicate_service_module=os.getenv("M4_DUPLICATE_SERVICE_MODULE", "app.services.duplicate_service"),
        reroute_hook=os.getenv("M4_REROUTE_HOOK", ""),
        mount_heatmap=_bool("M5_MOUNT_HEATMAP", True),
        mount_duplicate_routes=_bool("M5_MOUNT_DUPLICATE_ROUTES", True),
    )
