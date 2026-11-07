from __future__ import annotations

import time

from fastapi.testclient import TestClient

from app.main import create_app

YOUTUBE_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"


def wait_for_job(client: TestClient, job_id: str, timeout: float = 15.0) -> dict:
    deadline = time.time() + timeout
    last: dict = {}
    while time.time() < deadline:
        response = client.get(f"/api/jobs/{job_id}")
        assert response.status_code == 200, response.text
        last = response.json()
        if last["status"] in {"ready", "error", "expired"}:
            return last
        time.sleep(0.05)
    raise AssertionError(f"Job did not finish in time: {last}")


def test_health_reports_capabilities(base_settings) -> None:
    app = create_app(base_settings)
    with TestClient(app) as client:
        response = client.get("/api/health")
        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "ok"
        assert payload["ytdlp"] is True
        assert payload["ffmpeg"] is True


def test_extract_reports_only_reported_formats(base_settings) -> None:
    app = create_app(base_settings)
    with TestClient(app) as client:
        response = client.post("/api/extract", json={"url": YOUTUBE_URL})
        assert response.status_code == 200, response.text
        data = response.json()

        assert data["platform"] == "youtube"
        assert data["title"] == "Test public video"
        assert data["uploader"] == "Clipwell Test Channel"
        assert data["durationSeconds"] == 125
        assert data["sourceUrl"] == YOUTUBE_URL
        assert data["expiresInSeconds"] > 0
        assert data["isLive"] is False

        assert [option["id"] for option in data["videoOptions"]] == ["v1080", "v720", "v360"]
        assert data["videoOptions"][0]["isOriginal"] is True
        assert data["videoOptions"][0]["height"] == 1080
        assert [option["id"] for option in data["audioOptions"]] == [
            "audio-original",
            "audio-mp3",
        ]
        assert [track["lang"] for track in data["captions"]] == ["en", "es"]
        assert data["captions"][0]["auto"] is False
        assert data["captions"][1]["auto"] is True


def test_full_download_and_caption_workflow(base_settings) -> None:
    app = create_app(base_settings)
    with TestClient(app) as client:
        extracted = client.post("/api/extract", json={"url": YOUTUBE_URL}).json()
        media_id = extracted["mediaId"]

        created = client.post(
            "/api/download",
            json={"mediaId": media_id, "optionId": "v1080"},
        )
        assert created.status_code == 200, created.text
        job = created.json()
        assert job["status"] in {"queued", "downloading", "processing"}
        assert job["downloadUrl"] is None

        finished = wait_for_job(client, job["jobId"])
        assert finished["status"] == "ready", finished
        assert finished["progress"] == 100
        assert finished["filename"] == "test-public-video.mp4"
        assert finished["sizeBytes"] == len(b"fake-media-bytes" * 2048)
        assert finished["downloadUrl"] == f"/api/jobs/{job['jobId']}/file"

        file_response = client.get(finished["downloadUrl"])
        assert file_response.status_code == 200
        assert file_response.content == b"fake-media-bytes" * 2048
        assert "attachment" in file_response.headers["content-disposition"]
        assert "test-public-video.mp4" in file_response.headers["content-disposition"]
        assert file_response.headers["content-type"] == "video/mp4"
        assert file_response.headers["cache-control"] == "private, no-store"

        captions = client.post(
            f"/api/media/{media_id}/captions",
            json={"lang": "en", "auto": False},
        )
        assert captions.status_code == 200, captions.text
        payload = captions.json()
        assert payload["lang"] == "en"
        assert payload["label"] == "English"
        assert payload["auto"] is False
        assert "Hello from the test." in payload["text"]
        assert payload["text"].count("Hello from the test.") == 1
        assert "00:00:00,000 --> 00:00:04,000" in payload["srt"]
        assert "Second caption line." in payload["srt"]


def test_mp3_download_returns_audio_file(base_settings) -> None:
    app = create_app(base_settings)
    with TestClient(app) as client:
        extracted = client.post("/api/extract", json={"url": YOUTUBE_URL}).json()
        created = client.post(
            "/api/download",
            json={"mediaId": extracted["mediaId"], "optionId": "audio-mp3"},
        )
        assert created.status_code == 200, created.text
        finished = wait_for_job(client, created.json()["jobId"])
        assert finished["status"] == "ready", finished
        assert finished["filename"].endswith(".mp3")

        file_response = client.get(finished["downloadUrl"])
        assert file_response.status_code == 200
        assert file_response.headers["content-type"] == "audio/mpeg"


def test_extract_rejects_unsupported_and_dangerous_urls(base_settings) -> None:
    app = create_app(base_settings)
    with TestClient(app) as client:
        unsupported = client.post("/api/extract", json={"url": "https://example.com/video"})
        assert unsupported.status_code == 422
        assert unsupported.json()["error"]["code"] == "unsupported_platform"

        ssrf = client.post("/api/extract", json={"url": "http://127.0.0.1/watch?v=abc"})
        assert ssrf.status_code == 422
        assert ssrf.json()["error"]["code"] == "unsupported_platform"

        photo = client.post(
            "/api/extract",
            json={"url": "https://www.tiktok.com/@creator/photo/1234567890"},
        )
        assert photo.status_code == 422
        assert photo.json()["error"]["code"] == "not_media"


def test_platform_block_is_reported_without_leaking_output(base_settings) -> None:
    app = create_app(base_settings)
    with TestClient(app) as client:
        response = client.post(
            "/api/extract",
            json={"url": "https://www.youtube.com/watch?v=blocked"},
        )
        assert response.status_code == 502
        error = response.json()["error"]
        assert error["code"] == "platform_blocked"
        assert "yt-dlp" not in error["message"]
        assert "Traceback" not in error["message"]


def test_unknown_format_and_job_are_rejected(base_settings) -> None:
    app = create_app(base_settings)
    with TestClient(app) as client:
        extracted = client.post("/api/extract", json={"url": YOUTUBE_URL}).json()

        bad_format = client.post(
            "/api/download",
            json={"mediaId": extracted["mediaId"], "optionId": "v9999"},
        )
        assert bad_format.status_code == 422
        assert bad_format.json()["error"]["code"] == "format_not_found"

        missing_job = client.get("/api/jobs/abcdefghij")
        assert missing_job.status_code == 404
        assert missing_job.json()["error"]["code"] == "job_not_found"

        bad_caption = client.post(
            f"/api/media/{extracted['mediaId']}/captions",
            json={"lang": "fr", "auto": False},
        )
        assert bad_caption.status_code == 404
        assert bad_caption.json()["error"]["code"] == "captions_unavailable"


def test_rate_limit_returns_retry_after(base_settings) -> None:
    limited = base_settings.model_copy(
        update={"rate_extract_per_minute": 1, "temp_dir": base_settings.temp_dir + "-limited"}
    )
    app = create_app(limited)
    with TestClient(app) as client:
        first = client.post("/api/extract", json={"url": YOUTUBE_URL})
        assert first.status_code == 200
        second = client.post("/api/extract", json={"url": YOUTUBE_URL})
        assert second.status_code == 429
        payload = second.json()["error"]
        assert payload["code"] == "rate_limited"
        assert payload["retryAfterSeconds"] >= 1
        assert int(second.headers["retry-after"]) >= 1


def test_request_body_limit(base_settings) -> None:
    limited = base_settings.model_copy(
        update={"max_request_body_bytes": 1024, "temp_dir": base_settings.temp_dir + "-body"}
    )
    app = create_app(limited)
    with TestClient(app) as client:
        response = client.post("/api/extract", json={"url": "https://youtube.com/" + "a" * 3000})
        assert response.status_code == 413
        assert response.json()["error"]["code"] == "payload_too_large"


def test_expired_download_cannot_be_fetched(base_settings) -> None:
    expired = base_settings.model_copy(
        update={"download_ttl_seconds": 1, "temp_dir": base_settings.temp_dir + "-expired"}
    )
    app = create_app(expired)
    with TestClient(app) as client:
        extracted = client.post("/api/extract", json={"url": YOUTUBE_URL}).json()
        created = client.post(
            "/api/download",
            json={"mediaId": extracted["mediaId"], "optionId": "v720"},
        )
        assert created.status_code == 200
        finished = wait_for_job(client, created.json()["jobId"])
        assert finished["status"] == "ready"

        time.sleep(1.2)

        status = client.get(f"/api/jobs/{created.json()['jobId']}")
        assert status.status_code == 200
        assert status.json()["status"] == "expired"

        file_response = client.get(f"/api/jobs/{created.json()['jobId']}/file")
        assert file_response.status_code == 410
        assert file_response.json()["error"]["code"] == "download_not_ready"


def test_security_headers_and_validation_envelope(base_settings) -> None:
    app = create_app(base_settings)
    with TestClient(app) as client:
        response = client.get("/api/health")
        assert response.headers["x-content-type-options"] == "nosniff"
        assert response.headers["x-frame-options"] == "DENY"
        assert response.headers["referrer-policy"] == "no-referrer"
        assert response.headers["cache-control"] == "no-store"

        invalid = client.post("/api/extract", json={"url": "not a url"})
        assert invalid.status_code == 422
        assert invalid.json()["error"]["code"] in {"invalid_url", "invalid_request"}
