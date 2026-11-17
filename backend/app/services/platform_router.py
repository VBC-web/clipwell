from __future__ import annotations


class PlatformRouter:
    """Routes a URL to the appropriate platform extractor (delegates to url_policy)."""

    def detect(self, url: str):
        from ..url_policy import detect_platform
        return detect_platform(url)
