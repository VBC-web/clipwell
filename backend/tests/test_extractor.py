from __future__ import annotations

import asyncio
from typing import Any

from app.extractor import YtDlpService
from app.url_policy import Platform


def test_tiktok_extraction_uses_ytdlp(monkeypatch, base_settings, media_info: dict[str, Any]) -> None:
    service = YtDlpService(base_settings)
    calls: list[tuple[str, Platform | None]] = []

    def forbidden_fast_path(*args, **kwargs):
        raise AssertionError("TikTok extraction must not use a third-party metadata API")

    async def fake_run_json(url: str, platform: Platform | None = None, **kwargs):
        calls.append((url, platform))
        return media_info

    monkeypatch.setattr(service, "_resolve_tiktok_fast", forbidden_fast_path, raising=False)
    monkeypatch.setattr(service, "_run_json", fake_run_json)

    result = asyncio.run(
        service.extract("https://www.tiktok.com/@creator/video/123456789", Platform.TIKTOK)
    )

    assert result.platform is Platform.TIKTOK
    assert calls == [("https://www.tiktok.com/@creator/video/123456789", Platform.TIKTOK)]
