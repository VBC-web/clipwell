# syntax=docker/dockerfile:1
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DENO_INSTALL=/opt/deno \
    PATH=/opt/deno/bin:$PATH

# System deps: ffmpeg (media), ca-certs (TLS), curl/unzip (Deno installer).
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg ca-certificates curl unzip \
    && rm -rf /var/lib/apt/lists/*

# Install Deno (JS runtime for yt-dlp EJS components). Pinned-ish via install.sh.
RUN curl -fsSL https://deno.land/install.sh | sh \
    && /opt/deno/bin/deno --version

WORKDIR /app

COPY requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt

# Install yt-dlp EJS remote components at build time is not possible (runtime fetch),
# but Deno must be on PATH for yt-dlp to detect it.
COPY app ./app

RUN useradd --system --uid 10001 --create-home clipwell \
    && mkdir -p /tmp/clipwell-api \
    && chown -R clipwell:clipwell /tmp/clipwell-api /opt/deno

USER clipwell

ENV ENVIRONMENT=production \
    ENABLE_DOCS=false \
    TEMP_DIR=/tmp/clipwell-api \
    USE_JS_RUNTIME=true \
    REMOTE_COMPONENTS=ejs:github

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=4).read()"]

# One worker is deliberate: jobs, media tokens and rate limits live in memory.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--proxy-headers", "--forwarded-allow-ips", "*", "--no-server-header", "--log-level", "info"]
PY