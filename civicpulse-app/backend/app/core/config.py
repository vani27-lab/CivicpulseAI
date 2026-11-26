"""Settings for the whole backend.

Every value can be changed with an environment variable (or a ".env" file in the
backend folder). Example: DATABASE_URL=... overrides `database_url` below.
"""
import os
from pathlib import Path
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(__file__).resolve().parent.parent.parent / ".env"


DB_FILE = Path(__file__).resolve().parent.parent.parent / "civicpulse.db"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(ENV_FILE), env_file_encoding="utf-8", extra="ignore")

    app_name: str = "CivicPulse AI"

    # Database (PostgreSQL + PostGIS or SQLite fallback)
    database_url: str = os.getenv("DATABASE_URL") or f"sqlite:///{DB_FILE.as_posix()}"

    # Login tokens (JWT)
    jwt_secret_key: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 8

    # Which website addresses may call the API from a browser
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # Where complaint photographs will be saved (used from Module 2 onward)
    upload_dir: str = "uploads"
    max_upload_mb: int = 10

    # Demo data
    seed_demo_data: bool = True
    demo_password: str = "Demo@1234"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
