from __future__ import annotations

import tempfile
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Clipwell API"
    environment: str = "development"
    log_level: str = "INFO"
    enable_docs: bool = True
    trust_proxy: bool = False

    allowed_origins: str = "http://localhost:4321,http://127.0.0.1:4321"

    ytdlp_path: str | None = None
    ffmpeg_location: str | None = None
    temp_dir: str | None = None

    extract_timeout_seconds: int = 60
    caption_timeout_seconds: int = 75
    job_timeout_seconds: int = 600
    socket_timeout_seconds: int = 20
    max_duration_seconds: int = 14_400
    max_file_size_mb: int = 500
    media_ttl_seconds: int = 1200
    download_ttl_seconds: int = 900
    caption_ttl_seconds: int = 900

    max_concurrent_jobs: int = 2
    max_pending_jobs: int = 20
    max_media_records: int = 500
    max_request_body_bytes: int = 65536
    max_caption_bytes: int = 2_000_000
    max_description_chars: int = 50_000

    rate_extract_per_minute: int = 12
    rate_download_per_minute: int = 6
    rate_status_per_minute: int = 180
    rate_caption_per_minute: int = 10
    rate_file_per_minute: int = 30

    @property
    def origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

    @property
    def temp_path(self) -> Path:
        if self.temp_dir:
            return Path(self.temp_dir).expanduser().resolve()
        return (Path(tempfile.gettempdir()) / "clipwell-api").resolve()

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
