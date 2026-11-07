from __future__ import annotations

import pytest

from app.subtitles import convert_subtitle, parse_cues, to_srt, to_text

VTT = """WEBVTT

NOTE This header is ignored.

cue-1
00:00:00.000 --> 00:00:02.500 align:start position:10%
<v Speaker>Hello &amp; welcome</v>

00:00:02.500 --> 00:00:04.000
Hello &amp; welcome

00:00:04.000 --> 00:00:06.200
Second <b>line</b>
"""

SRT = """1
00:00:01,000 --> 00:00:03,000
First SRT cue

2
00:01:02,250 --> 00:01:04,000
Second SRT cue
"""


def test_parse_vtt_cues_and_clean_markup() -> None:
    cues = parse_cues(VTT)
    assert len(cues) == 2
    assert cues[0].start_ms == 0
    assert cues[0].end_ms == 4000
    assert cues[0].text == "Hello & welcome"
    assert cues[1].text == "Second line"


def test_text_output_skips_repeated_rolling_lines() -> None:
    cues = parse_cues(VTT)
    assert to_text(cues) == "Hello & welcome\nSecond line"


def test_convert_subtitle_produces_srt() -> None:
    result = convert_subtitle(VTT)
    assert result.cue_count == 2
    assert "00:00:00,000 --> 00:00:04,000" in result.srt
    assert "Second line" in result.srt


def test_parse_srt_input() -> None:
    cues = parse_cues(SRT)
    assert [cue.text for cue in cues] == ["First SRT cue", "Second SRT cue"]
    assert cues[1].start_ms == 62_250
    assert to_srt(cues).startswith("1\n00:00:01,000 --> 00:00:03,000")


def test_short_webvtt_timestamps_without_hours() -> None:
    raw = "WEBVTT\n\n00:01.000 --> 00:03.500\nShort form\n"
    cues = parse_cues(raw)
    assert len(cues) == 1
    assert cues[0].start_ms == 1000
    assert cues[0].end_ms == 3500


def test_invalid_subtitle_content_raises() -> None:
    with pytest.raises(ValueError):
        convert_subtitle("This is only plain text with no timing.")
    with pytest.raises(ValueError):
        convert_subtitle("")
