from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from .url_policy import Platform

JobStatus = Literal["queued", "downloading", "processing", "ready", "error", "expired"]


class ApiModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class StrictRequest(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="forbid")


class ExtractRequest(StrictRequest):
    url: str = Field(min_length=1, max_length=2048)


class DownloadRequest(StrictRequest):
    media_id: str = Field(min_length=10, max_length=100, pattern=r"^[A-Za-z0-9_-]+$")
    option_id: str = Field(min_length=1, max_length=80, pattern=r"^[A-Za-z0-9_-]+$")


class CaptionRequest(StrictRequest):
    lang: str = Field(min_length=1, max_length=35, pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
    auto: bool = False


class VideoOptionOut(ApiModel):
    id: str
    label: str
    ext: str
    filesize_bytes: int | None = None
    note: str | None = None
    height: int | None = None
    fps: int | None = None
    is_original: bool = False


class AudioOptionOut(ApiModel):
    id: str
    label: str
    ext: str
    filesize_bytes: int | None = None
    note: str | None = None
    bitrate_kbps: int | None = None


class CaptionTrackOut(ApiModel):
    lang: str
    label: str
    auto: bool


class MediaOut(ApiModel):
    media_id: str
    platform: Platform
    source_url: str
    title: str
    description: str | None = None
    uploader: str | None = None
    duration_seconds: int | None = None
    thumbnail_url: str | None = None
    is_live: bool = False
    video_options: list[VideoOptionOut]
    audio_options: list[AudioOptionOut]
    captions: list[CaptionTrackOut]
    expires_in_seconds: int


class JobOut(ApiModel):
    job_id: str
    status: JobStatus
    progress: int = Field(ge=0, le=100)
    stage: str = ""
    message: str | None = None
    error: str | None = None
    filename: str | None = None
    size_bytes: int | None = None
    download_url: str | None = None
    expires_at: datetime | None = None


class CaptionOut(ApiModel):
    lang: str
    label: str
    auto: bool
    text: str
    srt: str
