"""
app/config.py
─────────────
All configuration is loaded from environment variables (or .env file).
No secrets are ever hardcoded here.
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ── Security ──────────────────────────────────────────────────────────
    secret_key: str = "change-me-to-a-random-secret"

    # ── Database ──────────────────────────────────────────────────────────
    # Default: SQLite (local/dev only).
    # For production set to a Postgres URL, e.g.:
    #   postgresql://user:pass@host/dbname
    database_url: str = "sqlite:///./captcha_testbed.db"

    # ── Rate limiting ─────────────────────────────────────────────────────
    rate_limit: str = "30/minute"

    # ── App behaviour ─────────────────────────────────────────────────────
    environment: str = "development"

    # Session cookie TTL (seconds).  Default: 10 minutes.
    session_ttl_seconds: int = 600

    # CAPTCHA session TTL (seconds).  Default: 10 minutes.
    captcha_ttl_seconds: int = 600

    # Grid CAPTCHA settings
    grid_size: int = 9          # total tiles in the grid
    grid_min_pos: int = 2       # minimum number of positive tiles
    grid_max_pos: int = 4       # maximum number of positive tiles

    # Available target categories for the grid CAPTCHA
    grid_categories: list[str] = ["bus", "car", "traffic_light", "bicycle", "hydrant"]


    # ── Paths (derived from project root) ────────────────────────────────
    # The project root is two levels above this file: TESTARENA/
    base_dir: Path = Path(__file__).resolve().parent.parent
    data_dir: Path = base_dir / "data"
    images_dir: Path = data_dir / "images"
    index_path: Path = data_dir / "index.json"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings singleton (loaded once at startup)."""
    return Settings()
