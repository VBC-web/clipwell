from __future__ import annotations

from typing import Any

from ..extractors.ytdlp_engine import YtDlpService


class ExtractionManager:
    """Thin facade over the yt-dlp engine (common extraction interface)."""

    def __init__(self, service: YtDlpService) -> None:
        self.service = service

    async def extract(self, url: str, platform: Any) -> Any:
        return await self.service.extract(url, platform)

    async def download(self, url, plan, workdir, on_progress):
        return await self.service.download(url, plan, workdir, on_progress)

    @property
    def available(self) -> bool:
        return self.service.available
