from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseExtractor(ABC):
    """Common interface every platform extractor implements."""

    @abstractmethod
    async def extract(self, url: str, platform: Any) -> Any:
        ...

    @abstractmethod
    async def download(self, url: str, plan: Any, workdir: Any, on_progress: Any) -> Any:
        ...

    @property
    @abstractmethod
    def available(self) -> bool:
        ...
