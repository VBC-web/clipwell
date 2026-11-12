from __future__ import annotations

import asyncio
import logging
import secrets
import shutil
from contextlib import asynccontextmanager
from typing import Any

from fastapi import APIRouter, FastAPI, Path, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from starlette.datastructures import MutableHeaders
from starlette.exceptions import HTTPException as StarletteHTTPException

from .config import Settings, get_settings
from .errors import AppError
from .extractor import YtDlpService
from .jobs import JobManager
from .media_store import MediaStore
from .models import (
    CaptionOut,
    CaptionRequest,
    DownloadRequest,
    ExtractRequest,
    FeedbackRequest,
    JobOut,
    MediaOut,
)
from .rate_limit import SlidingWindowLimiter, allow_request
from .url_policy import validate_url

logger = logging.getLogger("clipwell.api")

VERSION = "1.0.0"

_JobId = Path(min_length=10, max_length=100, pattern=r"^[A-Za-z0-9_-]+$")
_MediaId = Path(min_length=10, max_length=100, pattern=r"^[A-Za-z0-9_-]+$")


class BodyTooLarge(Exception):
    pass


class SecurityMiddleware:
    """Body-size enforcement plus response hardening for every API response."""

    def __init__(self, app: Any, settings: Settings) -> None:
        self.app = app
        self.settings = settings
        self.max_bytes = max(1, settings.max_request_body_bytes)

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = {key.lower(): value for key, value in scope.get("headers", [])}
        content_length = headers.get(b"content-length")
        if content_length:
            try:
                declared = int(content_length)
            except ValueError:
                declared = 0
            if declared > self.max_bytes:
                await JSONResponse(
                    {"error": {"code": "payload_too_large", "message": "The request body is too large."}},
                    status_code=413,
                )(scope, receive, send)
                return

        total = 0
        response_started = False

        async def limited_receive() -> Any:
            nonlocal total
            message = await receive()
            if message.get("type") == "http.request":
                total += len(message.get("body", b""))
                if total > self.max_bytes:
                    raise BodyTooLarge
            return message

        async def hardened_send(message: Any) -> None:
            nonlocal response_started
            if message["type"] == "http.response.start":
                response_started = True
                response_headers = MutableHeaders(scope=message)
                response_headers.setdefault("X-Content-Type-Options", "nosniff")
                response_headers.setdefault("X-Frame-Options", "DENY")
                response_headers.setdefault("Referrer-Policy", "no-referrer")
                response_headers.setdefault(
                    "Permissions-Policy", "geolocation=(), microphone=(), camera=()"
                )
                path = scope.get("path", "")
                if path.startswith("/api/"):
                    response_headers.setdefault("Cache-Control", "no-store")
                if self.settings.environment == "production":
                    response_headers.setdefault(
                        "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
                    )
            await send(message)

        try:
            await self.app(scope, limited_receive, hardened_send)
        except BodyTooLarge:
            if not response_started:
                await JSONResponse(
                    {"error": {"code": "payload_too_large", "message": "The request body is too large."}},
                    status_code=413,
                )(scope, receive, send)


def _state(request: Request) -> tuple[Settings, MediaStore, JobManager, YtDlpService, SlidingWindowLimiter]:
    app = request.app
    return (
        app.state.settings,
        app.state.store,
        app.state.jobs,
        app.state.service,
        app.state.limiter,
    )


router = APIRouter(prefix="/api")


@router.get("/health")
async def health(request: Request) -> dict[str, Any]:
    settings, _, _, service, _ = _state(request)
    return {
        "status": "ok" if service.available else "degraded",
        "service": settings.app_name,
        "version": VERSION,
        "environment": settings.environment,
        "ytdlp": service.available,
        "ffmpeg": service.ffmpeg_available,
    }


@router.post("/extract", response_model=MediaOut)
async def extract(payload: ExtractRequest, request: Request) -> MediaOut:
    settings, store, _, service, limiter = _state(request)
    allow_request(limiter, request, settings, "extract", settings.rate_extract_per_minute)

    validated = validate_url(payload.url)
    extraction = await service.extract(validated.url, validated.platform)

    record = store.add(
        platform=extraction.platform,
        source_url=extraction.source_url,
        title=extraction.title,
        description=extraction.description,
        uploader=extraction.uploader,
        duration_seconds=extraction.duration_seconds,
        thumbnail_url=extraction.thumbnail_url,
        is_live=extraction.is_live,
        options=extraction.options,
        captions=extraction.captions,
    )
    return record.to_out()


@router.post("/download", response_model=JobOut)
async def create_download(payload: DownloadRequest, request: Request) -> JobOut:
    settings, store, jobs, _, limiter = _state(request)
    allow_request(limiter, request, settings, "download", settings.rate_download_per_minute)

    record = store.get(payload.media_id)
    job = jobs.create(record, payload.option_id)
    return job.to_out()


@router.get("/jobs/{job_id}", response_model=JobOut)
async def job_status(request: Request, job_id: str = _JobId) -> JobOut:
    settings, _, jobs, _, limiter = _state(request)
    allow_request(limiter, request, settings, "status", settings.rate_status_per_minute)
    return jobs.get(job_id).to_out()


@router.get("/jobs/{job_id}/file")
async def job_file(request: Request, job_id: str = _JobId) -> FileResponse:
    settings, _, jobs, _, limiter = _state(request)
    allow_request(limiter, request, settings, "file", settings.rate_file_per_minute)

    path, filename, media_type = jobs.get_file(job_id)
    return FileResponse(
        path,
        media_type=media_type,
        filename=filename,
        headers={
            "Cache-Control": "private, no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.post("/media/{media_id}/captions", response_model=CaptionOut)
async def media_captions(
    payload: CaptionRequest,
    request: Request,
    media_id: str = _MediaId,
) -> CaptionOut:
    settings, store, _, service, limiter = _state(request)
    allow_request(limiter, request, settings, "caption", settings.rate_caption_per_minute)

    record = store.get(media_id)
    if (payload.lang, payload.auto) not in record.caption_keys:
        raise AppError(
            "captions_unavailable",
            "That caption track was not listed for this media. Read the link again to refresh the tracks.",
            status_code=404,
        )

    workdir = settings.temp_path / "captions" / secrets.token_urlsafe(12)
    try:
        result = await service.fetch_subtitle(
            record.source_url,
            payload.lang,
            payload.auto,
            workdir,
        )
    finally:
        shutil.rmtree(workdir, ignore_errors=True)

    track = next(
        (
            item
            for item in record.captions
            if item.lang == payload.lang and item.auto == payload.auto
        ),
        None,
    )
    return CaptionOut(
        lang=payload.lang,
        label=track.label if track else payload.lang,
        auto=payload.auto,
        text=result.text,
        srt=result.srt,
    )


async def _app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    headers = {"Retry-After": str(exc.retry_after)} if exc.retry_after else None
    return JSONResponse(exc.to_payload(), status_code=exc.status_code, headers=headers)


async def _validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    logger.info("Rejected invalid request to %s", request.url.path)
    return JSONResponse(
        {
            "error": {
                "code": "invalid_request",
                "message": "The request was not valid. Check the link or chosen format and try again.",
            }
        },
        status_code=422,
    )


async def _http_error_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    if request.url.path.startswith("/api/"):
        code = "not_found" if exc.status_code == 404 else "http_error"
        message = (
            "That API endpoint does not exist."
            if exc.status_code == 404
            else "The request could not be completed."
        )
        return JSONResponse({"error": {"code": code, "message": message}}, status_code=exc.status_code)
    return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)


async def _unexpected_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error on %s", request.url.path)
    return JSONResponse(
        {
            "error": {
                "code": "server_error",
                "message": "An unexpected server error occurred. Try again in a moment.",
            }
        },
        status_code=500,
    )


@router.post("/feedback")
async def submit_feedback(payload: FeedbackRequest, request: Request) -> dict[str, str]:
    settings, _, _, _, limiter = _state(request)
    allow_request(limiter, request, settings, "feedback", 5)

    import json as _json
    import time as _time

    record = {
        "receivedAt": _time.strftime("%Y-%m-%dT%H:%M:%SZ", _time.gmtime()),
        "category": payload.category,
        "message": payload.message,
        "url": payload.url,
        "email": payload.email,
    }
    settings.temp_path.mkdir(parents=True, exist_ok=True, mode=0o700)
    target = settings.temp_path / "feedback.jsonl"
    with target.open("a", encoding="utf-8") as handle:
        handle.write(_json.dumps(record, ensure_ascii=False) + "\n")

    return {"status": "ok"}

def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        settings.temp_path.mkdir(parents=True, exist_ok=True, mode=0o700)
        service = YtDlpService(settings)
        store = MediaStore(settings)
        jobs = JobManager(settings, service)

        app.state.settings = settings
        app.state.service = service
        app.state.store = store
        app.state.jobs = jobs
        app.state.limiter = SlidingWindowLimiter()

        jobs.cleanup_orphans()
        logger.info(
            "Clipwell API started (environment=%s, ytdlp=%s, ffmpeg=%s, temp=%s)",
            settings.environment,
            service.available,
            service.ffmpeg_available,
            settings.temp_path,
        )

        stop = asyncio.Event()

        async def clean_periodically() -> None:
            while not stop.is_set():
                try:
                    await asyncio.wait_for(stop.wait(), timeout=60)
                except asyncio.TimeoutError:
                    pass
                if stop.is_set():
                    break
                try:
                    store.purge_expired()
                    jobs.purge_expired()
                except Exception:
                    logger.exception("Temporary file cleanup failed")

        cleaner = asyncio.create_task(clean_periodically(), name="clipwell-cleanup")
        try:
            yield
        finally:
            stop.set()
            cleaner.cancel()
            await asyncio.gather(cleaner, return_exceptions=True)
            await jobs.shutdown()
            logger.info("Clipwell API stopped")

    docs_enabled = settings.enable_docs
    app = FastAPI(
        title=settings.app_name,
        version=VERSION,
        description="Public-media extraction and temporary download service for Clipwell.",
        docs_url="/api/docs" if docs_enabled else None,
        redoc_url=None,
        openapi_url="/api/openapi.json" if docs_enabled else None,
        lifespan=lifespan,
    )

    app.add_middleware(SecurityMiddleware, settings=settings)
    if settings.origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.origins,
            allow_credentials=False,
            allow_methods=["GET", "POST", "OPTIONS"],
            allow_headers=["Content-Type", "Accept"],
            expose_headers=["Content-Disposition"],
            max_age=600,
        )

    app.add_exception_handler(AppError, _app_error_handler)
    app.add_exception_handler(RequestValidationError, _validation_error_handler)
    app.add_exception_handler(StarletteHTTPException, _http_error_handler)
    app.add_exception_handler(Exception, _unexpected_error_handler)

    app.include_router(router)

    @app.get("/")
    async def root() -> dict[str, Any]:
        return {
            "service": settings.app_name,
            "version": VERSION,
            "docs": "/api/docs" if docs_enabled else None,
            "health": "/api/health",
        }

    return app


app = create_app()
