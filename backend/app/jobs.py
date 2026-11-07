from __future__ import annotations

import asyncio
import logging
import re
import secrets
import shutil
import time
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from .config import Settings
from .errors import AppError
from .extractor import YtDlpService
from .formats import OptionPlan
from .media_store import MediaRecord
from .models import JobOut, JobStatus

logger = logging.getLogger("clipwell.jobs")

_ACTIVE_STATUSES: frozenset[JobStatus] = frozenset({"queued", "downloading", "processing"})
_SLUG_RE = re.compile(r"[^a-z0-9]+")


def _slugify(value: str, fallback: str = "clipwell-download") -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii").lower()
    slug = _SLUG_RE.sub("-", ascii_value).strip("-")
    return (slug[:80].rstrip("-") or fallback)


@dataclass(slots=True)
class Job:
    id: str
    media_id: str
    option_id: str
    title: str
    source_url: str
    plan: OptionPlan
    status: JobStatus = "queued"
    progress: int = 0
    stage: str = "Waiting for a download slot"
    message: str | None = None
    error: str | None = None
    filename: str | None = None
    size_bytes: int | None = None
    path: Path | None = None
    media_type: str | None = None
    created_at: float = field(default_factory=time.monotonic)
    created_wall: float = field(default_factory=time.time)
    expires_at: float | None = None
    expires_wall: float | None = None
    task: asyncio.Task[None] | None = None

    @property
    def active(self) -> bool:
        return self.status in _ACTIVE_STATUSES

    def to_out(self) -> JobOut:
        download_url = (
            f"/api/jobs/{self.id}/file"
            if self.status == "ready" and self.path is not None and self.path.is_file()
            else None
        )
        expires = (
            datetime.fromtimestamp(self.expires_wall, tz=timezone.utc)
            if self.expires_wall
            else None
        )
        return JobOut(
            job_id=self.id,
            status=self.status,
            progress=max(0, min(100, self.progress)),
            stage=self.stage,
            message=self.message,
            error=self.error,
            filename=self.filename,
            size_bytes=self.size_bytes,
            download_url=download_url,
            expires_at=expires,
        )


class JobManager:
    """Owns downloads, temp files and their expiries.

    State is intentionally in-process. Run a single API worker, or replace this
    manager with a shared queue before scaling horizontally.
    """

    def __init__(self, settings: Settings, service: YtDlpService) -> None:
        self.settings = settings
        self.service = service
        self._jobs: dict[str, Job] = {}
        self._semaphore = asyncio.Semaphore(max(1, settings.max_concurrent_jobs))
        self._tasks: set[asyncio.Task[None]] = set()
        self._shutting_down = False

    @property
    def jobs_dir(self) -> Path:
        return self.settings.temp_path / "jobs"

    def create(self, media: MediaRecord, option_id: str) -> Job:
        plan = media.options.get(option_id)
        if plan is None:
            raise AppError(
                "format_not_found",
                "That format is no longer available. Read the link again to refresh the options.",
                status_code=422,
            )

        active = sum(1 for job in self._jobs.values() if job.active)
        if active >= self.settings.max_pending_jobs:
            raise AppError(
                "queue_full",
                "The download queue is full. Wait a minute and try again.",
                status_code=429,
                retry_after=20,
            )

        job = Job(
            id=secrets.token_urlsafe(18),
            media_id=media.id,
            option_id=plan.id,
            title=media.title,
            source_url=media.source_url,
            plan=plan,
        )
        self._jobs[job.id] = job
        task = asyncio.create_task(self._run(job), name=f"clipwell-job-{job.id}")
        job.task = task
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return job

    async def _run(self, job: Job) -> None:
        record = self._jobs.get(job.id)
        if record is None:
            return

        try:
            async with self._semaphore:
                if self._shutting_down:
                    raise AppError("server_restarting", "The server is restarting. Try again.", 503)

                job.status = "downloading"
                job.progress = 1
                job.stage = "Downloading from the platform"
                job.message = "Keep this tab open. Larger videos can take a minute."

                workdir = self.jobs_dir / job.id

                def report(percent: int) -> None:
                    job.progress = max(1, min(90, round(percent * 0.9)))

                path = await self.service.download(
                    job.source_url,
                    job.plan,
                    workdir,
                    report,
                )

                job.status = "processing"
                job.progress = 95
                job.stage = "Preparing the file"

                ext = path.suffix.lower().lstrip(".") or job.plan.ext
                job.path = path
                job.size_bytes = path.stat().st_size
                job.filename = f"{_slugify(job.title)}.{ext}"
                job.media_type = self.service.guess_media_type(job.filename)
                job.progress = 100
                job.status = "ready"
                job.stage = "Your file is ready"
                job.message = "The temporary file is removed automatically after it expires."
                job.expires_at = time.monotonic() + self.settings.download_ttl_seconds
                job.expires_wall = time.time() + self.settings.download_ttl_seconds

        except asyncio.CancelledError:
            job.status = "error"
            job.stage = "The download could not be completed"
            job.error = "The server stopped the download. Try again."
            job.expires_wall = time.time() + self.settings.download_ttl_seconds
            job.expires_at = time.monotonic() + self.settings.download_ttl_seconds
            self._cleanup_workdir(job)
            raise
        except AppError as exc:
            job.status = "error"
            job.stage = "The download could not be completed"
            job.error = exc.message
            job.progress = max(0, min(job.progress, 99))
            job.expires_wall = time.time() + self.settings.download_ttl_seconds
            job.expires_at = time.monotonic() + self.settings.download_ttl_seconds
            self._cleanup_workdir(job)
        except Exception:
            logger.exception("Unexpected download failure for job %s", job.id)
            job.status = "error"
            job.stage = "The download could not be completed"
            job.error = "An unexpected server error stopped the download. Try again."
            job.expires_wall = time.time() + self.settings.download_ttl_seconds
            job.expires_at = time.monotonic() + self.settings.download_ttl_seconds
            self._cleanup_workdir(job)

    def _cleanup_workdir(self, job: Job) -> None:
        job.path = None
        shutil.rmtree(self.jobs_dir / job.id, ignore_errors=True)

    def _refresh(self, job: Job) -> None:
        if (
            job.status == "ready"
            and job.expires_at is not None
            and time.monotonic() >= job.expires_at
        ):
            job.status = "expired"
            job.stage = "This download has expired"
            job.error = "This download link has expired. Start a new download."
            job.path = None
            job.expires_at = None
            job.expires_wall = None
            shutil.rmtree(self.jobs_dir / job.id, ignore_errors=True)

    def get(self, job_id: str) -> Job:
        job = self._jobs.get(job_id)
        if job is None:
            raise AppError(
                "job_not_found",
                "That download could not be found. Start a new download.",
                status_code=404,
            )
        self._refresh(job)
        return job

    def get_file(self, job_id: str) -> tuple[Path, str, str]:
        job = self.get(job_id)
        if job.status == "error":
            raise AppError(
                "download_failed",
                job.error or "That download did not complete.",
                status_code=409,
            )
        if job.status != "ready" or job.path is None or job.expires_at is None:
            raise AppError(
                "download_not_ready",
                "That file is not ready anymore. Start a new download.",
                status_code=410,
            )
        if not job.path.is_file():
            job.status = "expired"
            raise AppError(
                "download_expired",
                "The temporary file was already cleaned up. Start a new download.",
                status_code=410,
            )
        if not job.path.resolve().is_relative_to(self.jobs_dir.resolve()):
            raise AppError("download_failed", "The prepared file failed a safety check.", 500)
        return job.path, job.filename or job.path.name, job.media_type or "application/octet-stream"

    def purge_expired(self) -> int:
        now = time.monotonic()
        removed = 0
        for job_id, job in list(self._jobs.items()):
            if job.active:
                continue

            self._refresh(job)

            file_expired = job.expires_at is not None and now >= job.expires_at
            stale = now - job.created_at > max(self.settings.download_ttl_seconds + 3_600, 3_600)
            if file_expired or stale:
                shutil.rmtree(self.jobs_dir / job_id, ignore_errors=True)
                del self._jobs[job_id]
                removed += 1

        # Sweep abandoned directories that have no in-memory job (for example
        # after a crash or a container restart).
        if self.jobs_dir.exists():
            active_ids = {job_id for job_id, job in self._jobs.items() if job.active}
            cutoff = time.time() - 3_600
            for directory in self.jobs_dir.iterdir():
                if not directory.is_dir() or directory.name in active_ids:
                    continue
                try:
                    if directory.stat().st_mtime < cutoff:
                        shutil.rmtree(directory, ignore_errors=True)
                except OSError:
                    continue
        return removed

    def cleanup_orphans(self) -> None:
        if not self.jobs_dir.exists():
            return
        for directory in self.jobs_dir.iterdir():
            if directory.is_dir():
                shutil.rmtree(directory, ignore_errors=True)

    async def shutdown(self) -> None:
        self._shutting_down = True
        for job in self._jobs.values():
            if job.task and not job.task.done():
                job.task.cancel()
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        self.cleanup_orphans()
