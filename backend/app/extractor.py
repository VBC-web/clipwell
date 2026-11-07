from __future__ import annotations

import asyncio
import logging
import mimetypes
import os
import re
import shutil
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlsplit

from .config import Settings
from .errors import AppError
from .formats import OptionPlan, build_options
from .models import CaptionTrackOut
from .subtitles import SubtitleResult, convert_subtitle
from .url_policy import PLATFORMS, Platform

logger = logging.getLogger("clipwell.extractor")

_PROGRESS_RE = re.compile(r"\[download\]\s+(\d{1,3}(?:\.\d+)?)%")
_LANG_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,34}$")
_CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_MEDIA_EXT_RE = re.compile(r"^[a-z0-9]{1,6}$")

_ERROR_RULES: list[tuple[re.Pattern[str], str, str, int]] = [
    (
        re.compile(r"sign in to confirm|not a bot|confirm your age|cookies", re.I),
        "platform_blocked",
        "This platform is asking for a browser sign-in or bot check. Clipwell does not use accounts "
        "or cookies, so this public link cannot be read right now. Try again later or use the "
        "platform's own download option.",
        502,
    ),
    (
        re.compile(r"private|login required|members[- ]only|subscriber|age[- ]restricted", re.I),
        "private_media",
        "This post is private, members-only or age-restricted. Clipwell only handles public media.",
        422,
    ),
    (
        re.compile(r"not available in your country|geo[- ]?block|geo[- ]?restrict", re.I),
        "geo_blocked",
        "This video is not available from the server's region. Clipwell cannot bypass geographic "
        "restrictions.",
        422,
    ),
    (
        re.compile(r"rate.?limit|too many requests|http error 429", re.I),
        "platform_rate_limited",
        "The platform is rate-limiting requests from this server. Give it a few minutes and try again.",
        429,
    ),
    (
        re.compile(r"unsupported url|no video formats|no video|no suitable|no formats", re.I),
        "unsupported_media",
        "That page does not expose a public video stream. Paste a direct link to a public video, reel, "
        "clip or VOD.",
        422,
    ),
    (
        re.compile(r"video unavailable|not available|removed|deleted|does not exist|http error 404", re.I),
        "unavailable",
        "That post is unavailable. It may have been deleted, made private or moved.",
        422,
    ),
    (
        re.compile(r"timed out|timeout", re.I),
        "extract_timeout",
        "The platform took too long to respond. Try again in a moment.",
        504,
    ),
    (
        re.compile(r"ffmpeg (?:is )?not (?:found|installed)|ffprobe", re.I),
        "service_unavailable",
        "The server is missing FFmpeg, so this format cannot be prepared. Contact the site operator.",
        503,
    ),
]


@dataclass(slots=True)
class Extraction:
    platform: Platform
    source_url: str
    title: str
    description: str | None
    uploader: str | None
    duration_seconds: int | None
    thumbnail_url: str | None
    is_live: bool
    options: list[OptionPlan]
    captions: list[CaptionTrackOut]


def _as_int(value: Any) -> int | None:
    try:
        number = int(float(value))
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


def _clean_text(value: Any, limit: int, *, multiline: bool = True) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.replace("\r\n", "\n").replace("\r", "\n")
    text = _CONTROL_RE.sub("", text)
    if not multiline:
        text = re.sub(r"\s+", " ", text)
    else:
        text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()
    if not text:
        return None
    return text[:limit].rstrip()


def _safe_thumbnail(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    candidate = value.strip()
    if not candidate or len(candidate) > 2048:
        return None
    try:
        parsed = urlsplit(candidate)
    except ValueError:
        return None
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
        return None
    return candidate


def _is_live(info: dict[str, Any]) -> bool:
    return bool(info.get("is_live")) or str(info.get("live_status") or "") in {
        "is_live",
        "is_upcoming",
    }


def _command_for_path(path: str) -> list[str]:
    lower = path.lower()
    if lower.endswith(".py"):
        return [sys.executable, path]
    if lower.endswith((".cmd", ".bat")):
        return [os.environ.get("COMSPEC", "cmd.exe"), "/c", path]
    return [path]


def _resolve_ytdlp(settings: Settings) -> list[str] | None:
    configured = (settings.ytdlp_path or "").strip()
    if configured:
        path = Path(configured).expanduser()
        if path.is_file():
            return _command_for_path(str(path.resolve()))
        logger.error("Configured yt-dlp path does not exist: %s", path)
        return None

    executable = shutil.which("yt-dlp")
    if executable:
        return [executable]

    try:
        import yt_dlp  # noqa: F401
    except ImportError:
        return None
    return [sys.executable, "-m", "yt_dlp"]


def _resolve_ffmpeg(settings: Settings) -> str | None:
    configured = (settings.ffmpeg_location or "").strip()
    if configured:
        path = Path(configured).expanduser()
        if path.is_dir():
            candidate = path / ("ffmpeg.exe" if os.name == "nt" else "ffmpeg")
            return str(candidate) if candidate.is_file() else None
        return str(path) if path.is_file() else None
    return shutil.which("ffmpeg")


def _classify_error(stderr: str) -> AppError:
    for pattern, code, message, status in _ERROR_RULES:
        if pattern.search(stderr):
            return AppError(code, message, status_code=status)
    return AppError(
        "extract_failed",
        "The platform returned an error while reading this link. It may be temporarily unavailable.",
        status_code=502,
    )


def _caption_tracks(info: dict[str, Any]) -> list[CaptionTrackOut]:
    tracks: list[CaptionTrackOut] = []
    seen: set[tuple[str, bool]] = set()

    sources = (
        (info.get("subtitles"), False),
        (info.get("automatic_captions"), True),
    )
    for source, is_auto in sources:
        if not isinstance(source, dict):
            continue
        for lang, entries in source.items():
            if not isinstance(lang, str) or not _LANG_RE.match(lang):
                continue
            if (lang, is_auto) in seen or not isinstance(entries, list):
                continue

            chosen = None
            for preferred_ext in ("vtt", "srt"):
                chosen = next(
                    (
                        entry
                        for entry in entries
                        if isinstance(entry, dict) and str(entry.get("ext")).lower() == preferred_ext
                    ),
                    None,
                )
                if chosen is not None:
                    break
            if chosen is None:
                chosen = next(
                    (
                        entry
                        for entry in entries
                        if isinstance(entry, dict) and str(entry.get("ext")).lower() in {"vtt", "srt"}
                    ),
                    None,
                )
            if chosen is None:
                continue

            label = _clean_text(chosen.get("name"), 120, multiline=False) or lang
            seen.add((lang, is_auto))
            tracks.append(CaptionTrackOut(lang=lang, label=label, auto=is_auto))

    # Manual tracks first so the frontend's default is the better source.
    tracks.sort(key=lambda track: (track.auto, track.label.lower()))
    return tracks[:60]


class YtDlpService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._command = _resolve_ytdlp(settings)
        self._ffmpeg = _resolve_ffmpeg(settings)
        if self._command is None:
            logger.error(
                "yt-dlp is not available. Install it or set YTDLP_PATH to a working executable."
            )
        if self._ffmpeg is None:
            logger.warning("FFmpeg is not available. Merged video and MP3 options will be disabled.")

    @property
    def available(self) -> bool:
        return self._command is not None

    @property
    def ffmpeg_available(self) -> bool:
        return self._ffmpeg is not None

    def _base_args(self) -> list[str]:
        args = [
            "--ignore-config",
            "--no-warnings",
            "--no-cache-dir",
            "--no-playlist",
            "--no-mtime",
            "--socket-timeout",
            str(self.settings.socket_timeout_seconds),
        ]
        if self._ffmpeg:
            args.extend(["--ffmpeg-location", self._ffmpeg])
        return args

    def _env(self) -> dict[str, str]:
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUTF8"] = "1"
        env["NO_COLOR"] = "1"
        return env

    def _popen_kwargs(self) -> dict[str, Any]:
        if os.name == "nt":
            flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            return {"creationflags": flags} if flags else {}
        return {"start_new_session": True}

    async def _terminate(self, process: asyncio.subprocess.Process) -> None:
        if process.returncode is not None:
            return
        if os.name == "nt":
            try:
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(process.pid)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=10,
                    check=False,
                )
            except (OSError, subprocess.SubprocessError):
                process.kill()
        else:
            try:
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
            except (OSError, ProcessLookupError):
                process.kill()
        try:
            await asyncio.wait_for(process.wait(), timeout=5)
        except (asyncio.TimeoutError, ProcessLookupError):
            pass

    async def _run_json(self, url: str) -> dict[str, Any]:
        if self._command is None:
            raise AppError(
                "service_unavailable",
                "The extraction service is not configured. The site operator needs to install yt-dlp.",
                status_code=503,
            )

        args = self._base_args() + [
            "--extractor-retries",
            "1",
            "--retries",
            "2",
            "--dump-single-json",
            "--skip-download",
            url,
        ]
        command = self._command + args

        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=self._env(),
                **self._popen_kwargs(),
            )
        except (FileNotFoundError, OSError):
            logger.exception("Could not start yt-dlp")
            raise AppError(
                "service_unavailable",
                "The extraction service is unavailable. Try again later.",
                status_code=503,
            ) from None

        started = time.monotonic()
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.settings.extract_timeout_seconds,
            )
        except asyncio.TimeoutError:
            await self._terminate(process)
            raise AppError(
                "extract_timeout",
                "The platform took too long to respond. Try again in a moment.",
                status_code=504,
            ) from None

        elapsed = time.monotonic() - started
        stderr_text = stderr.decode("utf-8", "replace")
        logger.info("yt-dlp extract exited %s in %.1fs", process.returncode, elapsed)

        if process.returncode != 0:
            logger.warning("yt-dlp extract failed: %s", stderr_text[-3000:])
            raise _classify_error(stderr_text)

        output = stdout.decode("utf-8", "replace").strip()
        if not output:
            raise AppError(
                "extract_failed",
                "The platform returned an empty response. Try the link again.",
                status_code=502,
            )

        import json

        try:
            info = json.loads(output)
        except json.JSONDecodeError:
            logger.warning("yt-dlp returned non-JSON output: %s", output[-1000:])
            raise AppError(
                "extract_failed",
                "The platform returned an unexpected response. Try the link again.",
                status_code=502,
            ) from None

        if not isinstance(info, dict):
            raise AppError("extract_failed", "The platform returned an unexpected response.", 502)
        if info.get("_type") == "playlist" or info.get("entries"):
            raise AppError(
                "playlist_unsupported",
                "Playlist links are not supported. Paste a direct link to one video.",
                status_code=422,
            )
        return info

    async def extract(self, url: str, platform: Platform) -> Extraction:
        info = await self._run_json(url)

        if _is_live(info):
            raise AppError(
                "live_unsupported",
                "This is a live stream. Clipwell saves completed videos, not live broadcasts. "
                "Try a replay or VOD link instead.",
                status_code=422,
            )

        duration = _as_int(info.get("duration"))
        if duration and duration > self.settings.max_duration_seconds:
            hours = self.settings.max_duration_seconds / 3600
            raise AppError(
                "media_too_long",
                f"This video is longer than the {hours:g}-hour limit. Shorten it or choose a smaller clip.",
                status_code=422,
            )

        title = (
            _clean_text(info.get("title"), 300, multiline=False)
            or f"{PLATFORMS[platform].name} public video"
        )
        description = _clean_text(info.get("description"), self.settings.max_description_chars)
        uploader = (
            _clean_text(
                info.get("uploader")
                or info.get("channel")
                or info.get("creator")
                or info.get("uploader_id"),
                200,
                multiline=False,
            )
            or None
        )

        thumbnail = _safe_thumbnail(info.get("thumbnail"))
        if thumbnail is None:
            thumbnails = info.get("thumbnails")
            if isinstance(thumbnails, list):
                for entry in reversed(thumbnails):
                    if isinstance(entry, dict):
                        thumbnail = _safe_thumbnail(entry.get("url"))
                        if thumbnail:
                            break

        options = build_options(
            info,
            duration_seconds=duration,
            ffmpeg_available=self.ffmpeg_available,
        )
        captions = _caption_tracks(info)

        return Extraction(
            platform=platform,
            source_url=url,
            title=title,
            description=description,
            uploader=uploader,
            thumbnail_url=thumbnail,
            is_live=False,
            duration_seconds=duration,
            options=options,
            captions=captions,
        )

    async def download(
        self,
        url: str,
        plan: OptionPlan,
        workdir: Path,
        on_progress: Callable[[int], None],
    ) -> Path:
        if self._command is None:
            raise AppError(
                "service_unavailable",
                "The download service is not configured. The site operator needs to install yt-dlp.",
                status_code=503,
            )

        workdir.mkdir(parents=True, exist_ok=True, mode=0o700)
        template = str(workdir / "media.%(ext)s")
        args = self._base_args() + [
            "--newline",
            "--progress",
            "--no-part",
            "--restrict-filenames",
            "--max-filesize",
            str(self.settings.max_file_size_bytes),
            "-f",
            plan.selector,
            "-o",
            template,
        ]

        if plan.kind == "video":
            if not self.ffmpeg_available:
                raise AppError(
                    "service_unavailable",
                    "This server cannot merge video and audio because FFmpeg is missing.",
                    status_code=503,
                )
            args.extend(["--merge-output-format", "mp4"])
        elif plan.audio_format:
            if not self.ffmpeg_available:
                raise AppError(
                    "service_unavailable",
                    "This server cannot convert audio because FFmpeg is missing.",
                    status_code=503,
                )
            args.extend(["-x", "--audio-format", plan.audio_format])
            if plan.audio_quality:
                args.extend(["--audio-quality", plan.audio_quality])

        args.append(url)

        try:
            process = await asyncio.create_subprocess_exec(
                *(self._command + args),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=self._env(),
                **self._popen_kwargs(),
            )
        except (FileNotFoundError, OSError):
            logger.exception("Could not start yt-dlp download")
            raise AppError(
                "service_unavailable",
                "The download service is unavailable. Try again later.",
                status_code=503,
            ) from None

        async def consume() -> tuple[str, str]:
            stderr_chunks: list[bytes] = []

            async def read_stderr() -> None:
                assert process.stderr is not None
                while True:
                    chunk = await process.stderr.read(8192)
                    if not chunk:
                        break
                    if sum(len(item) for item in stderr_chunks) < 64_000:
                        stderr_chunks.append(chunk)

            stderr_task = asyncio.create_task(read_stderr())
            assert process.stdout is not None
            try:
                while True:
                    line = await process.stdout.readline()
                    if not line:
                        break
                    text = line.decode("utf-8", "replace")
                    match = _PROGRESS_RE.search(text)
                    if match:
                        try:
                            percent = max(0, min(100, int(float(match.group(1)))))
                        except ValueError:
                            continue
                        try:
                            on_progress(percent)
                        except Exception:  # Progress reporting must never break a download.
                            logger.exception("Progress callback failed")
            finally:
                await stderr_task
            code = await process.wait()
            return code, b"".join(stderr_chunks).decode("utf-8", "replace")

        try:
            return_code, stderr_text = await asyncio.wait_for(
                consume(), timeout=self.settings.job_timeout_seconds
            )
        except asyncio.TimeoutError:
            await self._terminate(process)
            raise AppError(
                "download_timeout",
                "The download took too long and was stopped. Try a smaller format or try again later.",
                status_code=504,
            ) from None

        if return_code != 0:
            logger.warning("yt-dlp download failed: %s", stderr_text[-3000:])
            raise _classify_error(stderr_text)

        candidates = [
            path
            for path in workdir.iterdir()
            if path.is_file() and not path.name.endswith((".part", ".ytdl", ".temp"))
        ]
        if not candidates:
            raise AppError(
                "download_failed",
                "The platform finished without producing a file. Try a different format.",
                status_code=502,
            )

        expected = workdir / f"media.{plan.ext}"
        target = expected if expected.is_file() else max(candidates, key=lambda path: path.stat().st_size)

        resolved = target.resolve()
        if not resolved.is_relative_to(workdir.resolve()):
            raise AppError("download_failed", "The prepared file failed a safety check.", 500)

        size = resolved.stat().st_size
        if size <= 0:
            raise AppError("download_failed", "The prepared file was empty. Try again.", 502)
        if size > self.settings.max_file_size_bytes:
            resolved.unlink(missing_ok=True)
            raise AppError(
                "file_too_large",
                f"The finished file is larger than the {self.settings.max_file_size_mb} MB limit.",
                status_code=413,
            )
        return resolved

    async def fetch_subtitle(
        self,
        url: str,
        lang: str,
        auto: bool,
        workdir: Path,
    ) -> SubtitleResult:
        if self._command is None:
            raise AppError(
                "service_unavailable",
                "The caption service is not configured. The site operator needs to install yt-dlp.",
                status_code=503,
            )

        workdir.mkdir(parents=True, exist_ok=True, mode=0o700)
        args = self._base_args() + [
            "--skip-download",
            "--write-auto-subs" if auto else "--write-subs",
            "--sub-langs",
            lang,
            "--sub-format",
            "vtt/srt/best",
            "--no-post-overwrites",
            "-o",
            str(workdir / "caption.%(ext)s"),
            url,
        ]

        try:
            process = await asyncio.create_subprocess_exec(
                *(self._command + args),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=self._env(),
                **self._popen_kwargs(),
            )
        except (FileNotFoundError, OSError):
            raise AppError("service_unavailable", "The caption service is unavailable.", 503) from None

        try:
            _, stderr = await asyncio.wait_for(
                process.communicate(), timeout=self.settings.caption_timeout_seconds
            )
        except asyncio.TimeoutError:
            await self._terminate(process)
            raise AppError(
                "caption_timeout",
                "The platform took too long to provide that caption track.",
                status_code=504,
            ) from None

        if process.returncode != 0:
            stderr_text = stderr.decode("utf-8", "replace")
            logger.warning("yt-dlp caption failed: %s", stderr_text[-2000:])
            raise _classify_error(stderr_text)

        files = sorted(
            (
                path
                for path in workdir.iterdir()
                if path.is_file() and path.suffix.lower() in {".vtt", ".srt"}
            ),
            key=lambda path: path.stat().st_size,
            reverse=True,
        )
        if not files:
            raise AppError(
                "captions_unavailable",
                "The platform did not return that caption track. It may have been removed.",
                status_code=404,
            )

        target = files[0]
        if target.stat().st_size > self.settings.max_caption_bytes:
            raise AppError(
                "captions_too_large",
                "That caption track is too large to process.",
                status_code=413,
            )

        raw = target.read_text(encoding="utf-8-sig", errors="replace")
        try:
            return convert_subtitle(raw)
        except ValueError:
            raise AppError(
                "captions_unavailable",
                "That caption track did not contain readable timed text.",
                status_code=422,
            ) from None

    @staticmethod
    def guess_media_type(filename: str) -> str:
        media_type, _ = mimetypes.guess_type(filename)
        return media_type or "application/octet-stream"
