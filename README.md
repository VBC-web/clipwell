# Clipwell

**Public media, saved cleanly.**

Clipwell is a multi-platform video downloader with an Astro marketing site and a separately deployable FastAPI backend. It extracts public media metadata with `yt-dlp`, exposes only formats the platform actually reports, and serves finished files from short-lived temporary storage.

The site includes dedicated pages for Instagram, Facebook, YouTube, TikTok, Kick, Twitch and X (Twitter), plus About, Contact, Privacy, Terms, Copyright, DMCA and Disclaimer pages.

---

## Important honesty note

The application, validation, job system, caption conversion and API contract are implemented and covered by automated tests. The end-to-end download workflow in the test suite uses a **fake `yt-dlp` executable**, so it does not depend on platform availability.

Live extraction from real platforms is inherently fragile. During development, YouTube returned a “Sign in to confirm you’re not a bot” challenge and TikTok timed out from this network. Clipwell deliberately does **not** attach cookies, use account sessions, rotate proxies or attempt DRM/access-control bypasses. When a platform blocks the server, the API returns a specific error instead of a fake success. Expect real-world platform behavior to change over time; keep `yt-dlp` updated.

---

## Features

- Seven platform-specific downloader pages with unique copy, FAQs and SEO metadata.
- Homepage with universal URL input, paste button, platform auto-detection and correct-downloader redirect.
- Client-side and server-side URL validation, including platform mismatch guidance.
- SSRF-resistant domain allowlist. Profiles, playlists, photo posts, live channels and private content are rejected with actionable messages.
- Real metadata only: title, uploader, duration, thumbnail, description and caption tracks from the source.
- Video options derived from reported streams, marked with the best available quality.
- Original audio and FFmpeg-generated MP3 options only when an audio-only stream exists.
- Manual and auto-generated caption tracks, converted to SRT and plain text.
- Asynchronous download jobs with progress polling, concurrency limits, timeouts and automatic temp-file cleanup.
- Rate limiting, body-size limits, file-size limits, no shell execution and client-safe error envelopes.
- Dark/light theme, responsive navigation, accessible loading/error/success states.
- Static Astro build, sitemap, robots.txt, JSON-LD, canonical URLs, Open Graph/Twitter cards and security headers.
- Docker Compose deployment with Nginx same-origin API proxying.

---

## Architecture

```
Browser
  │
  ├── Astro static site (Nginx)
  │      └── /api/* proxied to FastAPI
  │
  └── FastAPI (single worker)
         ├── URL allowlist + platform detection
         ├── yt-dlp subprocess (no shell)
         ├── FFmpeg (merge / audio conversion)
         ├── In-memory media tokens + job manager
         └── Temporary files (auto-expired)
```

The browser never receives a `yt-dlp` format selector. It receives an opaque media token and server-issued option IDs. Downloads are created from that server-side record only.

### Repository layout

```
clipwell/
├── backend/
│   ├── app/
│   │   ├── main.py          FastAPI app, routes, middleware, error handlers
│   │   ├── config.py        Environment settings and limits
│   │   ├── url_policy.py    Allowlist, normalization, media-path checks
│   │   ├── extractor.py     yt-dlp subprocess, metadata, downloads, captions
│   │   ├── formats.py       Honest option plans from reported streams
│   │   ├── media_store.py   Expiring in-memory media records
│   │   ├── jobs.py          Async download jobs and temp-file lifecycle
│   │   ├── subtitles.py     VTT/SRT parsing and conversion
│   │   ├── rate_limit.py    Sliding-window limiter
│   │   ├── models.py        Pydantic request/response schemas
│   │   └── errors.py        Client-safe error type
│   ├── tests/               URL, format, subtitle and API-flow tests
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/      Header, footer, downloader, legal UI
│   │   ├── data/            Site constants and platform-specific copy
│   │   ├── layouts/         Base and legal layouts
│   │   ├── lib/             API client, URL detection, SEO helpers
│   │   ├── pages/           Homepage, platform pages, legal pages
│   │   └── styles/          Design tokens and Tailwind styles
│   ├── nginx.conf
│   ├── Dockerfile
│   └── .env.example
├── scripts/                 Reproducible OG/icon asset generation
├── docker-compose.yml
└── .env.example
```

---

## Requirements

- Node.js 22+ and npm 10+
- Python 3.12+ (tested with 3.14)
- `yt-dlp` on `PATH` (or `YTDLP_PATH`)
- `ffmpeg` on `PATH` (or `FFMPEG_LOCATION`) for merged video and MP3 output

On Windows, make sure `yt-dlp` and `ffmpeg` are available to the same shell that starts the backend.

---

## Local development

### 1. Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
copy .env.example .env      # Windows
# cp .env.example .env      # macOS/Linux
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Health check: <http://127.0.0.1:8000/api/health>
API docs (development): <http://127.0.0.1:8000/api/docs>

### 2. Frontend

In a second terminal:

```bash
cd frontend
npm install
copy .env.example .env      # Windows
# cp .env.example .env      # macOS/Linux
npm run dev
```

Open <http://localhost:4321>. The default development API base is `http://127.0.0.1:8000`.

### 3. Verification

```bash
cd backend && python -m pytest -q
cd frontend && npm run check && npm run build
```

---

## Configuration

### Frontend (build-time)

| Variable | Default | Purpose |
| --- | --- | --- |
| `PUBLIC_SITE_URL` | `https://clipwell.app` | Canonical URLs, sitemap, Open Graph, JSON-LD |
| `PUBLIC_API_BASE_URL` | `http://127.0.0.1:8000` in dev | API origin. **Empty string means same origin** and is used by the bundled Nginx setup. |

Frontend variables are embedded during `astro build`. Rebuild after changing them.

### Backend (runtime)

See `backend/.env.example` for the full list. The most important settings:

| Variable | Default | Purpose |
| --- | --- | --- |
| `ENVIRONMENT` | `development` | Enables HSTS in `production` |
| `ENABLE_DOCS` | `true` | Exposes `/api/docs` and OpenAPI JSON |
| `ALLOWED_ORIGINS` | localhost dev origins | Comma-separated CORS origins; empty when same-origin |
| `TRUST_PROXY` | `false` | Trust `X-Forwarded-For`; only behind a proxy that overwrites it |
| `YTDLP_PATH` | `PATH` lookup | Explicit yt-dlp executable |
| `FFMPEG_LOCATION` | `PATH` lookup | Explicit ffmpeg executable or directory |
| `TEMP_DIR` | system temp / `clipwell-api` | Temporary media and job directories |
| `MAX_FILE_SIZE_MB` | `500` | Finished-file ceiling |
| `MAX_DURATION_SECONDS` | `14400` | Four-hour source ceiling |
| `MAX_CONCURRENT_JOBS` | `2` | Active yt-dlp downloads |
| `MAX_PENDING_JOBS` | `20` | Queue ceiling |
| `MEDIA_TTL_SECONDS` | `1200` | Media-token lifetime |
| `DOWNLOAD_TTL_SECONDS` | `900` | Ready-file lifetime |
| `RATE_*_PER_MINUTE` | see `.env.example` | Per-IP request ceilings |

---

## API

All errors use:

```json
{
  "error": {
    "code": "platform_blocked",
    "message": "Client-safe explanation.",
    "retryAfterSeconds": 12,
    "platform": "youtube"
  }
}
```

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/health` | Liveness plus yt-dlp/FFmpeg capability flags |
| `POST` | `/api/extract` | Validate a URL and return real metadata/options |
| `POST` | `/api/download` | Start a job from `mediaId` + server-issued `optionId` |
| `GET` | `/api/jobs/{jobId}` | Poll job status and progress |
| `GET` | `/api/jobs/{jobId}/file` | Download the finished temporary file |
| `POST` | `/api/media/{mediaId}/captions` | Fetch and convert one caption track |

The API does not accept arbitrary format selectors, output paths or yt-dlp arguments.

---

## Tests

The backend suite covers:

- URL normalization, allowlisting, SSRF attempts, platform mismatch, photo/profile rejection.
- Honest format construction, size estimates, original-quality marking, FFmpeg-unavailable behavior.
- VTT/SRT parsing, duplicate rolling-caption removal, SRT/text conversion.
- Full extract → download → poll → file flow with a fake yt-dlp executable.
- MP3 flow, captions flow, expiry, rate limiting, body limits, security headers and error envelopes.

```bash
cd backend
python -m pytest -q
```

No real network extraction is required for the suite. When testing manually against real platforms, use your own public test links and expect platform bot checks to appear from data-centre IPs.

---

## Docker deployment

1. Copy the environment file and set your real domain:

   ```bash
   cp .env.example .env
   ```

2. Edit `.env`:

   ```dotenv
   PUBLIC_SITE_URL=https://your-domain.example
   PUBLIC_API_BASE_URL=
   ALLOWED_ORIGINS=
   ENABLE_DOCS=false
   ```

3. Build and start:

   ```bash
   docker compose up -d --build
   ```

4. Put a TLS-terminating reverse proxy in front of port `8080` (Caddy, Traefik, another Nginx, or a cloud load balancer). The bundled Nginx proxies `/api/` to the backend container on the private Compose network.

5. Check:

   ```bash
   curl http://localhost:8080/api/health
   ```

To expose the API on a different origin instead of same-origin proxying, set `PUBLIC_API_BASE_URL` and `ALLOWED_ORIGINS` appropriately, then rebuild the frontend image.

### Why one worker?

Media tokens, download jobs and rate-limit counters live in process memory. Running multiple Uvicorn workers or multiple backend replicas would break status polling and make limits inconsistent. Run exactly one backend worker. To scale horizontally later, replace the in-memory `MediaStore`, `JobManager` and `SlidingWindowLimiter` with Redis/queue-backed implementations.

### Temp storage

`/tmp/clipwell-api` is mounted as a named volume. The API removes expired jobs every minute and clears orphaned job directories at startup. You can point `TEMP_DIR` at a dedicated disk or tmpfs if you prefer; size it for at least `MAX_CONCURRENT_JOBS × MAX_FILE_SIZE_MB` plus headroom.

---

### Render

Use the included `render.yaml` as a Blueprint, or create a Docker web service manually with:

- Dockerfile path: `backend/Dockerfile`
- Docker context: `backend`
- Health check path: `/api/health`
- One instance only (do not scale horizontally)

Set `ALLOWED_ORIGINS` to your frontend origin. Render provides `PORT` automatically only for non-Docker services; the Dockerfile already listens on `8000`, so either keep the service port at `8000` or change the Dockerfile `CMD` to bind to `$PORT`.

### Railway

Railway can build from `backend/Dockerfile` using `backend/railway.json`. Create a service from the `backend` directory, set the environment variables from `backend/.env.example`, and keep the deployment to a single replica. The health check is configured for `/api/health`.

---

## Pre-launch checklist

This repository is complete code, but a public deployment still needs operator-specific decisions:

- [ ] Replace the placeholder domain `clipwell.app` and all `@clipwell.app` addresses in `frontend/src/data/site.ts`.
- [ ] Replace the legal name `Clipwell` if it is not your registered business name.
- [ ] Register a **DMCA designated agent** with the U.S. Copyright Office and update the DMCA page with the registration details and postal address.
- [ ] Have a qualified lawyer review the Privacy Policy, Terms, Copyright Policy, DMCA Policy and Disclaimer for your jurisdiction and business structure.
- [ ] Set the governing-law jurisdiction in the Terms; the current text intentionally leaves it generic.
- [ ] Confirm data-retention language matches your actual `TEMP_DIR`, logs and proxy configuration.
- [ ] Set `PUBLIC_SITE_URL`, `ALLOWED_ORIGINS`, `ENABLE_DOCS=false`, and a real TLS reverse proxy.
- [ ] Configure log retention. Application logs contain request paths and sanitized yt-dlp error tails, not media URLs from request bodies.
- [ ] Review platform terms and local copyright rules. Clipwell is a utility, not a licence to redistribute media.
- [ ] Add a license file if you plan to distribute the code.

The current legal pages are written as a serious starting point, not as jurisdiction-specific legal advice.

---

## Security model

- **Domain allowlist:** only the seven platform host families are accepted. Subdomain matching is boundary-aware, so `instagram.com.evil.example` is rejected.
- **No arbitrary URLs:** the backend re-validates every submitted URL before invoking yt-dlp. Private IPs, unusual ports, credentials in URLs, non-HTTP schemes, profiles and playlist pages are rejected.
- **No shell:** yt-dlp is invoked with `asyncio.create_subprocess_exec` and an argument list. URLs are passed as data, never interpolated into a shell string.
- **No credentials:** the service never accepts cookies, sessions, passwords or DRM keys, and does not attempt access-control bypasses.
- **Opaque formats:** the browser sends only a media token and option ID. Selectors remain server-side.
- **Limits:** request body, source duration, output file size, extraction time, download time, concurrency and per-IP rates are all bounded.
- **Temp lifecycle:** job directories are removed on failure, after file expiry, and at startup when orphaned. Paths are checked to remain inside the job directory.
- **Response hardening:** `nosniff`, frame denial, referrer policy, permissions policy, no-store API caching and production HSTS are applied by middleware. Nginx adds a CSP and its own headers.
- **Error hygiene:** raw yt-dlp stderr, internal paths and stack traces are logged server-side but never returned to the browser.

---

## Known limitations

- Platform bot checks, geo-blocks, login walls and breakage are outside the application's control. Clear errors are returned; no bypass is attempted.
- Live streams are rejected because the service saves completed files, not live broadcasts. Replays and VODs are supported.
- Some platforms expose no separate audio stream, so audio-only options are absent by design.
- Caption quality and availability come from the platform. Auto-generated tracks can contain recognition errors.
- The in-memory job system is intentionally single-instance. A restart invalidates active jobs and media tokens.
- Rate limiting uses client IPs. Behind a proxy, configure trusted forwarded headers carefully.
- The download endpoint streams a completed temp file; it does not support resumable range downloads beyond what your reverse proxy/Starlette provides.
