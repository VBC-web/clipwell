from __future__ import annotations

import asyncio
import json
import urllib.parse
import urllib.request
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
        re.compile(r"age[- ]?restrict|confirm your age|sign in to view|members only", re.I),
        "restricted_media",
        "This video requires an account, age verification or creator approval. Clipwell cannot bypass those restrictions.",
        422,
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

    def _resolve_cookies(self) -> str | None:
        if not self.settings.cookies_file:
            return None
        candidate = Path(self.settings.cookies_file).expanduser()
        if candidate.is_file():
            return str(candidate.resolve())
        backend_candidate = Path(__file__).resolve().parent.parent / self.settings.cookies_file
        if backend_candidate.is_file():
            return str(backend_candidate.resolve())
        return None

    def _base_args(self) -> list[str]:
        args = [
            "--no-warnings",
            "--no-cache-dir",
            "--no-playlist",
            "--no-mtime",
            "--socket-timeout",
            str(self.settings.socket_timeout_seconds),
        ]
        cookies = self._resolve_cookies()
        if cookies:
            args.extend(["--cookies", cookies])
        if self.settings.pot_provider_url:
            args.extend(["--extractor-args", f"youtubepot-bgutilhttp:base_url={self.settings.pot_provider_url}"])
        if self.settings.use_js_runtime:
            args.extend(["--js-runtimes", "node"])
        if self.settings.remote_components:
            args.extend(["--remote-components", self.settings.remote_components])
        if self.settings.force_ipv4:
            args.append("--force-ipv4")
        proxy = self.settings.http_proxy or self.settings.proxy_url
        if proxy:
            args.extend(["--proxy", proxy])
        if self._ffmpeg:
            args.extend(["--ffmpeg-location", self._ffmpeg])
        return args

    def _platform_args(self, url: str, platform: Platform | None = None) -> list[str]:
        args: list[str] = []
        lowered = url.lower()
        is_youtube = (platform is not None and platform.value == "youtube") or "youtube.com" in lowered or "youtu.be" in lowered
        is_tiktok = (platform is not None and platform.value == "tiktok") or "tiktok.com" in lowered
        is_twitter = (platform is not None and platform.value == "twitter") or "x.com" in lowered or "twitter.com" in lowered
        is_kick = (platform is not None and platform.value == "kick") or "kick.com" in lowered

        if is_youtube:
            args.extend(["--extractor-args", "youtube:player_client=android,web"])
            args.extend(["--user-agent", "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1"])
        elif is_tiktok:
            args.extend(["--extractor-args", f"tiktok:api_hostname={self.settings.tiktok_api_hostname}"])
            args.extend(["--user-agent", "TikTok 26.2.0 (iPhone; iOS 17.4; Scale/3.00)"])
            args.extend(["--add-headers", "Referer: https://www.tiktok.com/"])
        elif is_twitter:
            args.extend(["--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"])
        elif is_kick:
            args.extend(["--concurrent-fragments", "8"])
        return args

    async def _resolve_tiktok_fast(self, url: str) -> Extraction | None:
        """Try TikWM's lightweight JSON endpoint before falling back to yt-dlp."""

        def fetch() -> dict[str, Any] | None:
            endpoint = "https://www.tikwm.com/api/?url=" + urllib.parse.quote(url, safe="")
            request = urllib.request.Request(
                endpoint,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                    "Accept": "application/json",
                },
            )
            try:
                with urllib.request.urlopen(request, timeout=4) as response:
                    payload = json.loads(response.read().decode("utf-8", "replace"))
            except Exception:
                return None
            if not isinstance(payload, dict) or payload.get("code") not in (0, "0", None):
                return None
            data = payload.get("data")
            return data if isinstance(data, dict) else None

        data = await asyncio.to_thread(fetch)
        if not data:
            return None

        play = data.get("play") or data.get("wmplay") or data.get("hdplay")
        hdplay = data.get("hdplay")
        if not play and not hdplay:
            return None

        options: list[OptionPlan] = []
        if hdplay:
            options.append(
                OptionPlan(
                    id="vhd",
                    kind="video",
                    label="HD video",
                    ext="mp4",
                    selector=str(hdplay),
                    note="Direct CDN stream",
                    filesize_bytes=_as_int(data.get("size")),
                    height=_as_int(data.get("height")) or 1080,
                    is_original=True,
                )
            )
        if play and play != hdplay:
            options.append(
                OptionPlan(
                    id="vstd",
                    kind="video",
                    label="Standard video",
                    ext="mp4",
                    selector=str(play),
                    note="Direct CDN stream",
                    filesize_bytes=_as_int(data.get("size")),
                    height=_as_int(data.get("height")) or 720,
                    is_original=hdplay is None,
                )
            )
        if not options:
            return None

        title = _clean_text(data.get("title"), 300, multiline=False) or "TikTok public video"
        uploader = _clean_text(data.get("author", {}).get("nickname") if isinstance(data.get("author"), dict) else data.get("author"), 200, multiline=False)
        duration = _as_int(data.get("duration"))
        thumbnail = _safe_thumbnail(data.get("cover") or data.get("origin_cover"))
        return Extraction(
            platform=Platform.TIKTOK,
            source_url=url,
            title=title,
            description=_clean_text(data.get("title"), self.settings.max_description_chars),
            uploader=uploader,
            thumbnail_url=thumbnail,
            is_live=False,
            duration_seconds=duration,
            options=options,
            captions=[],
        )
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

    async def _run_json(self, url: str, platform: Platform | None = None, timeout: int | None = None, extra_args: list[str] | None = None) -> dict[str, Any]:
        if self._command is None:
            raise AppError(
                "service_unavailable",
                "The extraction service is not configured. The site operator needs to install yt-dlp.",
                status_code=503,
            )

        effective_timeout = timeout or self.settings.extract_timeout_seconds
        args = self._base_args() + self._platform_args(url, platform) + (extra_args or []) + [
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
                timeout=effective_timeout,
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

    async def _download_direct(self, url: str, target: Path, on_progress) -> None:
        def fetch() -> None:
            request = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                "Referer": "https://www.tiktok.com/",
                "Accept": "*/*",
            })
            with urllib.request.urlopen(request, timeout=60) as response, target.open("wb") as output:
                total = int(response.headers.get("Content-Length") or 0)
                downloaded = 0
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    output.write(chunk)
                    downloaded += len(chunk)
                    if total:
                        on_progress(max(1, min(99, int(downloaded / total * 100))))

        await asyncio.to_thread(fetch)
        on_progress(100)

    async def extract(self, url: str, platform: Platform) -> Extraction:
        if platform == Platform.TIKTOK:
            fast = await self._resolve_tiktok_fast(url)
            if fast is not None:
                return fast
            # Fallback to yt-dlp with a short timeout and alternate host.
            try:
                info = await self._run_json(url, platform, timeout=8)
            except AppError as exc:
                if exc.code != "extract_timeout":
                    raise
                info = await self._run_json(
                    url,
                    platform,
                    timeout=8,
                    extra_args=["--extractor-args", f"tiktok:api_hostname=api16-normal-c-useast1a.tiktokv.com"],
                )
        else:
            info = await self._run_json(url, platform)

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
        if plan.selector.startswith(("http://", "https://")):
            target = workdir / f"media.{plan.ext}"
            await self._download_direct(plan.selector, target, on_progress)
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
        args = self._base_args() + self._platform_args(url, None) + [
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
