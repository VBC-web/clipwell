from __future__ import annotations

import pytest

from app.errors import AppError
from app.url_policy import Platform, detect_platform, validate_url


@pytest.mark.parametrize(
    ("url", "platform"),
    [
        ("https://www.instagram.com/reel/ABC123/", Platform.INSTAGRAM),
        ("https://instagram.com/p/ABC123/", Platform.INSTAGRAM),
        ("https://www.facebook.com/watch/?v=123456", Platform.FACEBOOK),
        ("https://fb.watch/abcDEF/", Platform.FACEBOOK),
        ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", Platform.YOUTUBE),
        ("https://youtu.be/dQw4w9WgXcQ", Platform.YOUTUBE),
        ("https://www.youtube.com/shorts/dQw4w9WgXcQ", Platform.YOUTUBE),
        ("https://www.tiktok.com/@creator/video/1234567890", Platform.TIKTOK),
        ("https://vm.tiktok.com/ZMabc123/", Platform.TIKTOK),
        ("https://kick.com/video/1234-5678", Platform.KICK),
        ("https://kick.com/channel?clip=clip_abc", Platform.KICK),
        ("https://www.twitch.tv/videos/123456789", Platform.TWITCH),
        ("https://clips.twitch.tv/FunnyClipSlug", Platform.TWITCH),
        ("https://x.com/creator/status/1234567890", Platform.TWITTER),
        ("https://twitter.com/creator/status/1234567890", Platform.TWITTER),
    ],
)
def test_valid_public_media_urls(url: str, platform: Platform) -> None:
    result = validate_url(url)
    assert result.platform is platform
    assert result.url.startswith("https://")
    assert "#" not in result.url


def test_hostname_detection_is_not_substring_based() -> None:
    assert detect_platform("instagram.com") is Platform.INSTAGRAM
    assert detect_platform("cdn.instagram.com") is Platform.INSTAGRAM
    assert detect_platform("instagram.com.evil.example") is None
    assert detect_platform("evil-instagram.com") is None
    assert detect_platform("notyoutube.com") is None


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1/watch?v=abc",
        "http://localhost/watch?v=abc",
        "https://instagram.com.evil.example/reel/abc",
        "https://example.com/video/abc",
        "file:///etc/passwd",
        "ftp://youtube.com/watch?v=abc",
        "https://user:pass@youtube.com/watch?v=abc",
        "https://youtube.com:8443/watch?v=abc",
        "https://www.instagram.com/creator/",
        "https://www.tiktok.com/@creator/photo/1234567890",
        "https://www.youtube.com/@channel",
        "https://www.twitch.tv/somechannel",
        "https://x.com/creator",
    ],
)
def test_non_media_or_unsafe_urls_are_rejected(url: str) -> None:
    with pytest.raises(AppError) as caught:
        validate_url(url)
    assert caught.value.status_code in {422, 400}
    assert caught.value.code in {
        "invalid_url",
        "insecure_url",
        "unsupported_platform",
        "not_media",
    }


def test_control_characters_and_backslashes_are_rejected() -> None:
    for value in ("https://youtube.com/wa\ntch?v=abc", "https://youtube.com\\@evil.com/watch?v=abc"):
        with pytest.raises(AppError):
            validate_url(value)


def test_mismatch_reports_detected_platform_and_normalized_url() -> None:
    with pytest.raises(AppError) as caught:
        validate_url("https://youtu.be/abc123", Platform.TIKTOK)

    error = caught.value
    assert error.code == "platform_mismatch"
    assert error.platform == "youtube"
    assert error.normalized_url == "https://youtu.be/abc123"


def test_url_is_normalized_to_https_and_fragment_is_removed() -> None:
    result = validate_url("http://m.youtube.com/watch?v=abc&feature=share#t=10")
    assert result.url == "https://m.youtube.com/watch?v=abc&feature=share"


def test_scheme_less_url_is_accepted() -> None:
    result = validate_url("youtube.com/watch?v=abc123")
    assert result.url == "https://youtube.com/watch?v=abc123"
    assert result.platform is Platform.YOUTUBE
