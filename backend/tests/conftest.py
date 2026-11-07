from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from app.config import Settings

MEDIA_INFO: dict[str, Any] = {
    "id": "test-video",
    "title": "Test public video",
    "description": "A public test clip used to verify the Clipwell API.",
    "uploader": "Clipwell Test Channel",
    "duration": 125,
    "thumbnail": "https://example.com/thumb.jpg",
    "is_live": False,
    "formats": [
        {
            "format_id": "137",
            "ext": "mp4",
            "height": 1080,
            "fps": 30,
            "vcodec": "avc1.640028",
            "acodec": "none",
            "filesize": 10_000_000,
            "tbr": 4500,
            "protocol": "https",
        },
        {
            "format_id": "140",
            "ext": "m4a",
            "vcodec": "none",
            "acodec": "mp4a.40.2",
            "filesize": 2_000_000,
            "abr": 128,
            "protocol": "https",
        },
        {
            "format_id": "22",
            "ext": "mp4",
            "height": 720,
            "fps": 30,
            "vcodec": "avc1.4d401f",
            "acodec": "mp4a.40.2",
            "filesize": 5_000_000,
            "protocol": "https",
        },
        {
            "format_id": "18",
            "ext": "mp4",
            "height": 360,
            "fps": 30,
            "vcodec": "avc1.42001E",
            "acodec": "mp4a.40.2",
            "filesize": 2_000_000,
            "protocol": "https",
        },
        {
            "format_id": "storyboard",
            "ext": "mhtml",
            "height": 90,
            "vcodec": "none",
            "acodec": "none",
        },
    ],
    "subtitles": {
        "en": [{"ext": "vtt", "name": "English", "url": "https://example.com/en.vtt"}]
    },
    "automatic_captions": {
        "es": [
            {
                "ext": "vtt",
                "name": "Spanish (auto-generated)",
                "url": "https://example.com/es.vtt",
            }
        ]
    },
}


FAKE_SCRIPT = '''\
import sys
from pathlib import Path

FIXTURE = Path(__file__).with_name("fixture.json")
args = sys.argv[1:]
url = args[-1] if args else ""

if "blocked" in url:
    print("ERROR: Sign in to confirm you're not a bot.", file=sys.stderr)
    raise SystemExit(1)

if "--dump-single-json" in args:
    sys.stdout.write(FIXTURE.read_text(encoding="utf-8"))
    raise SystemExit(0)

def output_template() -> Path:
    return Path(args[args.index("-o") + 1])

def media_ext() -> str:
    if "--write-subs" in args or "--write-auto-subs" in args:
        return "vtt"
    if "-x" in args:
        return "mp3" if "mp3" in args else "m4a"
    return "mp4"

target = Path(str(output_template()).replace("%(ext)s", media_ext()))
target.parent.mkdir(parents=True, exist_ok=True)

if target.suffix.lower() == ".vtt":
    target.write_text(
        "WEBVTT\\n\\n"
        "00:00:00.000 --> 00:00:02.000\\nHello from the test.\\n\\n"
        "00:00:02.000 --> 00:00:04.000\\nHello from the test.\\n\\n"
        "00:00:04.000 --> 00:00:06.000\\nSecond caption line.\\n",
        encoding="utf-8",
    )
    print(f"[info] Writing video subtitles to: {target}")
else:
    target.write_bytes(b"fake-media-bytes" * 2048)
    print("[download]  50.0% of 32.00KiB at 1.00MiB/s")
    print("[download] 100.0% of 32.00KiB in 00:00")
raise SystemExit(0)
'''


@pytest.fixture
def media_info() -> dict[str, Any]:
    return json.loads(json.dumps(MEDIA_INFO))


@pytest.fixture
def fake_ytdlp(tmp_path: Path, media_info: dict[str, Any]) -> Path:
    script = tmp_path / "fake_ytdlp.py"
    script.write_text(FAKE_SCRIPT, encoding="utf-8")
    (tmp_path / "fixture.json").write_text(json.dumps(media_info), encoding="utf-8")
    return script


@pytest.fixture
def base_settings(tmp_path: Path, fake_ytdlp: Path) -> Settings:
    ffmpeg = tmp_path / "ffmpeg.exe"
    ffmpeg.write_bytes(b"")
    return Settings(
        environment="test",
        enable_docs=False,
        temp_dir=str(tmp_path / "temp"),
        ytdlp_path=str(fake_ytdlp),
        ffmpeg_location=str(ffmpeg),
        max_concurrent_jobs=2,
        max_pending_jobs=5,
        max_media_records=50,
        rate_extract_per_minute=100,
        rate_download_per_minute=100,
        rate_status_per_minute=1000,
        rate_caption_per_minute=100,
        rate_file_per_minute=100,
    )
