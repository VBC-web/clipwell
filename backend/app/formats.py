from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Literal

OptionKind = Literal["video", "audio"]

_EXT_RE = re.compile(r"^[a-z0-9]{1,6}$")

_HEIGHT_NOTES = {
    2160: "4K",
    1440: "2K",
    1080: "Full HD",
    720: "HD",
    480: "SD",
}

# Containers that are never a real downloadable media stream.
_DEAD_EXTS = {"mhtml", "none", ""}


@dataclass(frozen=True, slots=True)
class OptionPlan:
    """A server-side download plan. The selector never leaves the backend."""

    id: str
    kind: OptionKind
    label: str
    ext: str
    selector: str
    note: str | None = None
    filesize_bytes: int | None = None
    height: int | None = None
    fps: int | None = None
    is_original: bool = False
    bitrate_kbps: int | None = None
    audio_format: str | None = None
    audio_quality: str | None = None


def _as_int(value: Any) -> int | None:
    try:
        number = int(float(value))
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


def _size(fmt: dict[str, Any]) -> int | None:
    for key in ("filesize", "filesize_approx"):
        value = _as_int(fmt.get(key))
        if value:
            return value
    return None


def _has_video(fmt: dict[str, Any]) -> bool:
    codec = fmt.get("vcodec")
    return bool(codec) and str(codec).lower() != "none"


def _has_audio(fmt: dict[str, Any]) -> bool:
    codec = fmt.get("acodec")
    return bool(codec) and str(codec).lower() != "none"


def _is_usable(fmt: dict[str, Any]) -> bool:
    ext = str(fmt.get("ext") or "").lower()
    if ext in _DEAD_EXTS:
        return False
    protocol = str(fmt.get("protocol") or "").lower()
    return protocol not in {"mhtml", "data"}


def _clean_ext(value: Any) -> str:
    ext = str(value or "").lower().strip()
    return ext if _EXT_RE.match(ext) else "mp4"


def _video_score(fmt: dict[str, Any]) -> tuple[int, int, float, int]:
    codec = str(fmt.get("vcodec") or "").lower()
    h264 = 1 if codec.startswith(("avc1", "h264")) else 0
    return (
        h264,
        _as_int(fmt.get("fps")) or 0,
        float(fmt.get("tbr") or 0),
        _size(fmt) or 0,
    )


def _video_selector(height: int, ffmpeg_available: bool) -> str:
    if not ffmpeg_available:
        # Without FFmpeg only progressive (video+audio) streams can be saved.
        return f"best[height<={height}]"

    # Prefer H.264 + AAC so the merged MP4 plays everywhere. Fall back to any
    # MP4 stream, then to whatever the platform exposes at this ceiling.
    return (
        f"bestvideo[height<={height}][vcodec^=avc1]+bestaudio[ext=m4a]/"
        f"bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]/"
        f"bestvideo[height<={height}]+bestaudio/best[height<={height}]"
    )


def _audio_only_formats(formats: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [fmt for fmt in formats if _has_audio(fmt) and not _has_video(fmt) and _is_usable(fmt)]


def _audio_score(fmt: dict[str, Any]) -> tuple[float, int]:
    return (float(fmt.get("abr") or fmt.get("tbr") or 0), _size(fmt) or 0)


def _best_audio(formats: list[dict[str, Any]]) -> dict[str, Any] | None:
    audio = _audio_only_formats(formats)
    return max(audio, key=_audio_score) if audio else None


def build_options(
    info: dict[str, Any],
    *,
    duration_seconds: int | None = None,
    ffmpeg_available: bool = True,
) -> list[OptionPlan]:
    """Build honest format options from a yt-dlp info dictionary.

    Options are derived only from streams that yt-dlp actually reported. The
    backend never invents a resolution, and the opaque option id is the only
    value the browser can send back.
    """

    raw_formats = info.get("formats")
    formats: list[dict[str, Any]] = []
    if isinstance(raw_formats, list):
        formats = [fmt for fmt in raw_formats if isinstance(fmt, dict) and _is_usable(fmt)]
    if not formats and info.get("url"):
        formats = [info]

    by_height: dict[int, list[dict[str, Any]]] = {}
    for fmt in formats:
        if not _has_video(fmt):
            continue
        if not ffmpeg_available and not _has_audio(fmt):
            # A video-only stream cannot be saved without FFmpeg to merge audio.
            continue
        height = _as_int(fmt.get("height")) or _as_int(fmt.get("width"))
        if height:
            by_height.setdefault(height, []).append(fmt)

    best_audio = _best_audio(formats)
    best_audio_size = _size(best_audio) if best_audio else None

    heights = sorted(by_height, reverse=True)[:12]
    options: list[OptionPlan] = []
    max_height = heights[0] if heights else None

    for height in heights:
        candidates = by_height[height]
        best = max(candidates, key=_video_score)
        fps = _as_int(best.get("fps"))
        fps = fps if fps and fps > 30 else None

        label = f"{height}p{fps if fps else ''}"
        notes: list[str] = []
        if height == max_height:
            notes.append("Best available")
        if height in _HEIGHT_NOTES:
            notes.append(_HEIGHT_NOTES[height])
        if fps:
            notes.append(f"{fps} fps")

        if _has_audio(best):
            estimated = _size(best)
        else:
            video_size = _size(best)
            estimated = (
                video_size + best_audio_size
                if video_size and best_audio_size
                else video_size
            )

        options.append(
            OptionPlan(
                id=f"v{height}{'p' + str(fps) if fps else ''}",
                kind="video",
                label=label,
                ext="mp4",
                selector=_video_selector(height, ffmpeg_available),
                note=" · ".join(notes) or None,
                filesize_bytes=estimated,
                height=height,
                fps=fps,
                is_original=height == max_height,
            )
        )

    if best_audio is not None:
        native_ext = _clean_ext(best_audio.get("ext"))
        bitrate = _as_int(best_audio.get("abr")) or _as_int(best_audio.get("tbr"))
        options.append(
            OptionPlan(
                id="audio-original",
                kind="audio",
                label="Original audio",
                ext=native_ext,
                selector="bestaudio/best",
                note="No re-encoding",
                filesize_bytes=_size(best_audio),
                bitrate_kbps=bitrate,
                is_original=True,
            )
        )

        # MP3 is a real FFmpeg conversion, not a claim that the source offers MP3.
        if ffmpeg_available and native_ext != "mp3":
            estimated = (
                round(duration_seconds * 192_000 / 8)
                if duration_seconds and duration_seconds > 0
                else None
            )
            options.append(
                OptionPlan(
                    id="audio-mp3",
                    kind="audio",
                    label="MP3 audio",
                    ext="mp3",
                    selector="bestaudio/best",
                    note="Converted with FFmpeg",
                    filesize_bytes=estimated,
                    bitrate_kbps=192,
                    audio_format="mp3",
                    audio_quality="192K",
                )
            )

    return options
