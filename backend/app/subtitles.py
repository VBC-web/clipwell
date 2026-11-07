from __future__ import annotations

import html
import re
from dataclasses import dataclass

_TIMING_RE = re.compile(
    r"^\s*(?P<start>(?:\d{1,2}:)?\d{1,2}:\d{2}[.,]\d{1,3})\s*-->\s*"
    r"(?P<end>(?:\d{1,2}:)?\d{1,2}:\d{2}[.,]\d{1,3})(?:\s+.*)?$"
)
_TAG_RE = re.compile(r"<[^>]+>")
_ASS_OVERRIDE_RE = re.compile(r"\{\\[^}]*\}")
_TIMESTAMP_RE = re.compile(r"^(?:(?P<h>\d{1,2}):)?(?P<m>\d{1,2}):(?P<s>\d{2})[.,](?P<ms>\d{1,3})$")


@dataclass(frozen=True, slots=True)
class Cue:
    start_ms: int
    end_ms: int
    text: str


@dataclass(frozen=True, slots=True)
class SubtitleResult:
    text: str
    srt: str
    cue_count: int


def _timestamp_to_ms(value: str) -> int | None:
    match = _TIMESTAMP_RE.match(value.strip())
    if not match:
        return None
    hours = int(match.group("h") or 0)
    minutes = int(match.group("m"))
    seconds = int(match.group("s"))
    milliseconds = int(match.group("ms").ljust(3, "0"))
    return ((hours * 60 + minutes) * 60 + seconds) * 1000 + milliseconds


def _ms_to_srt(value: int) -> str:
    value = max(0, value)
    hours, remainder = divmod(value, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, milliseconds = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"


def _clean_line(value: str) -> str:
    text = _ASS_OVERRIDE_RE.sub("", value)
    text = _TAG_RE.sub("", text)
    text = html.unescape(text)
    text = text.replace("\u200b", "").replace("\ufeff", "")
    return re.sub(r"[ \t]+", " ", text).strip()


def parse_cues(raw: str) -> list[Cue]:
    """Parse WebVTT or SubRip content into ordered, de-duplicated cues."""

    if not raw or not raw.strip():
        return []

    normalized = raw.replace("\r\n", "\n").replace("\r", "\n").lstrip("\ufeff")
    blocks = re.split(r"\n{2,}", normalized)
    cues: list[Cue] = []

    for block in blocks:
        lines = [line for line in block.split("\n") if line.strip()]
        if not lines:
            continue
        if lines[0].strip().upper().startswith(("WEBVTT", "NOTE", "STYLE", "REGION")):
            continue

        timing_index = next(
            (index for index, line in enumerate(lines) if _TIMING_RE.match(line)), None
        )
        if timing_index is None:
            continue

        timing = _TIMING_RE.match(lines[timing_index])
        if timing is None:
            continue
        start = _timestamp_to_ms(timing.group("start"))
        end = _timestamp_to_ms(timing.group("end"))
        if start is None or end is None or end <= start:
            continue

        text_lines = [_clean_line(line) for line in lines[timing_index + 1 :]]
        text = "\n".join(line for line in text_lines if line).strip()
        if not text:
            continue

        # YouTube-style rolling captions repeat the previous line. Suppress it.
        if cues and cues[-1].text == text:
            previous = cues[-1]
            cues[-1] = Cue(previous.start_ms, max(previous.end_ms, end), previous.text)
            continue

        cues.append(Cue(start, end, text))

    return cues


def to_srt(cues: list[Cue]) -> str:
    blocks = []
    for index, cue in enumerate(cues, start=1):
        text = cue.text.replace("\r\n", "\n").strip()
        if not text:
            continue
        blocks.append(
            f"{index}\n{_ms_to_srt(cue.start_ms)} --> {_ms_to_srt(cue.end_ms)}\n{text}"
        )
    return "\n\n".join(blocks) + ("\n" if blocks else "")


def to_text(cues: list[Cue]) -> str:
    lines: list[str] = []
    previous = ""
    for cue in cues:
        text = cue.text.strip()
        if not text or text == previous:
            continue
        previous = text
        lines.append(text)
    return "\n".join(lines)


def convert_subtitle(raw: str) -> SubtitleResult:
    cues = parse_cues(raw)
    if not cues:
        raise ValueError("No timed caption cues were found in the subtitle file.")
    return SubtitleResult(text=to_text(cues), srt=to_srt(cues), cue_count=len(cues))
