from __future__ import annotations

from typing import Any

from app.formats import build_options


def test_video_options_are_sorted_and_marked(media_info: dict[str, Any]) -> None:
    options = build_options(media_info, duration_seconds=125, ffmpeg_available=True)
    video = [option for option in options if option.kind == "video"]
    audio = [option for option in options if option.kind == "audio"]

    assert [option.height for option in video] == [1080, 720, 360]
    assert [option.id for option in video] == ["v1080", "v720", "v360"]
    assert video[0].is_original is True
    assert "Best available" in (video[0].note or "")
    assert all(option.is_original is False for option in video[1:])
    assert all(option.ext == "mp4" for option in video)

    # 1080p is video-only, so its estimate adds the best separate audio stream.
    assert video[0].filesize_bytes == 12_000_000
    # 720p and 360p are progressive and use their own reported size.
    assert video[1].filesize_bytes == 5_000_000
    assert video[2].filesize_bytes == 2_000_000

    assert [option.id for option in audio] == ["audio-original", "audio-mp3"]
    assert audio[0].ext == "m4a"
    assert audio[0].bitrate_kbps == 128
    assert audio[0].filesize_bytes == 2_000_000
    assert audio[1].ext == "mp3"
    assert audio[1].bitrate_kbps == 192
    assert audio[1].filesize_bytes == 3_000_000
    assert audio[1].audio_format == "mp3"


def test_without_ffmpeg_only_progressive_video_and_no_mp3(
    media_info: dict[str, Any],
) -> None:
    options = build_options(media_info, duration_seconds=125, ffmpeg_available=False)
    video = [option for option in options if option.kind == "video"]
    audio = [option for option in options if option.kind == "audio"]

    # The 1080p stream is video-only and cannot be merged without FFmpeg.
    assert [option.height for option in video] == [720, 360]
    assert [option.id for option in audio] == ["audio-original"]
    assert all("bestvideo" not in option.selector for option in video)


def test_no_formats_produces_no_fake_options() -> None:
    assert build_options({"formats": []}) == []
    assert build_options({}) == []


def test_audio_only_media_does_not_invent_video() -> None:
    info = {
        "formats": [
            {"ext": "m4a", "vcodec": "none", "acodec": "mp4a", "abr": 96, "filesize": 5000}
        ]
    }
    options = build_options(info, duration_seconds=10)
    assert [option.kind for option in options] == ["audio", "audio"]
    assert build_options(info, duration_seconds=10, ffmpeg_available=False)[0].kind == "audio"
    assert len(build_options(info, duration_seconds=10, ffmpeg_available=False)) == 1


def test_high_frame_rate_is_reflected_in_label() -> None:
    info = {
        "formats": [
            {
                "ext": "mp4",
                "height": 1080,
                "fps": 60,
                "vcodec": "avc1",
                "acodec": "none",
                "filesize": 10,
            },
            {
                "ext": "m4a",
                "vcodec": "none",
                "acodec": "mp4a",
                "filesize": 5,
            },
        ]
    }
    video = [option for option in build_options(info, duration_seconds=5) if option.kind == "video"]
    assert video[0].label == "1080p60"
    assert video[0].fps == 60
