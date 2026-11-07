from __future__ import annotations

import secrets
import time
from dataclasses import dataclass, field

from .config import Settings
from .errors import AppError
from .formats import OptionPlan
from .models import AudioOptionOut, CaptionTrackOut, MediaOut, VideoOptionOut
from .url_policy import Platform


@dataclass(slots=True)
class MediaRecord:
    id: str
    platform: Platform
    source_url: str
    title: str
    description: str | None
    uploader: str | None
    duration_seconds: int | None
    thumbnail_url: str | None
    is_live: bool
    options: dict[str, OptionPlan]
    captions: list[CaptionTrackOut] = field(default_factory=list)
    caption_keys: frozenset[tuple[str, bool]] = frozenset()
    created_at: float = field(default_factory=time.monotonic)
    expires_at: float = 0.0

    def to_out(self) -> MediaOut:
        video = []
        audio = []
        for plan in self.options.values():
            if plan.kind == "video":
                video.append(
                    VideoOptionOut(
                        id=plan.id,
                        label=plan.label,
                        ext=plan.ext,
                        filesize_bytes=plan.filesize_bytes,
                        note=plan.note,
                        height=plan.height,
                        fps=plan.fps,
                        is_original=plan.is_original,
                    )
                )
            else:
                audio.append(
                    AudioOptionOut(
                        id=plan.id,
                        label=plan.label,
                        ext=plan.ext,
                        filesize_bytes=plan.filesize_bytes,
                        note=plan.note,
                        bitrate_kbps=plan.bitrate_kbps,
                    )
                )

        remaining = max(0, int(self.expires_at - time.monotonic()))
        return MediaOut(
            media_id=self.id,
            platform=self.platform,
            source_url=self.source_url,
            title=self.title,
            description=self.description,
            uploader=self.uploader,
            duration_seconds=self.duration_seconds,
            thumbnail_url=self.thumbnail_url,
            is_live=self.is_live,
            video_options=video,
            audio_options=audio,
            captions=self.captions,
            expires_in_seconds=remaining,
        )


class MediaStore:
    """Short-lived, in-memory record of extracted media.

    The browser receives a random token instead of a yt-dlp selector. A record
    is the only way to turn that token back into a server-side format plan.
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._records: dict[str, MediaRecord] = {}

    def add(
        self,
        *,
        platform: Platform,
        source_url: str,
        title: str,
        description: str | None,
        uploader: str | None,
        duration_seconds: int | None,
        thumbnail_url: str | None,
        is_live: bool,
        options: list[OptionPlan],
        captions: list[CaptionTrackOut],
    ) -> MediaRecord:
        self.purge_expired()
        self._make_room()

        record = MediaRecord(
            id=secrets.token_urlsafe(18),
            platform=platform,
            source_url=source_url,
            title=title,
            description=description,
            uploader=uploader,
            duration_seconds=duration_seconds,
            thumbnail_url=thumbnail_url,
            is_live=is_live,
            options={option.id: option for option in options},
            captions=list(captions),
            caption_keys=frozenset((track.lang, track.auto) for track in captions),
            expires_at=time.monotonic() + self.settings.media_ttl_seconds,
        )
        self._records[record.id] = record
        return record

    def get(self, media_id: str) -> MediaRecord:
        record = self._records.get(media_id)
        if record is None:
            raise AppError(
                "media_not_found",
                "This media record is not available. Read the link again to get fresh formats.",
                status_code=410,
            )
        if record.expires_at <= time.monotonic():
            self._records.pop(media_id, None)
            raise AppError(
                "media_expired",
                "This media record expired. Paste the link again to get fresh formats.",
                status_code=410,
            )
        return record

    def purge_expired(self) -> int:
        now = time.monotonic()
        expired = [key for key, record in self._records.items() if record.expires_at <= now]
        for key in expired:
            del self._records[key]
        return len(expired)

    def _make_room(self) -> None:
        limit = max(1, self.settings.max_media_records)
        while len(self._records) >= limit:
            oldest = min(self._records, key=lambda key: self._records[key].created_at)
            del self._records[oldest]

    def __len__(self) -> int:
        return len(self._records)
