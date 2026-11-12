from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from urllib.parse import urlsplit, urlunsplit

from .errors import AppError

MAX_URL_LENGTH = 2048
_CONTROL_OR_SPACE = re.compile(r"[\x00-\x20\x7f]")


class Platform(str, Enum):
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"
    KICK = "kick"
    TWITCH = "twitch"
    TWITTER = "twitter"


@dataclass(frozen=True, slots=True)
class PlatformSpec:
    key: Platform
    name: str
    hosts: tuple[str, ...]


PLATFORMS: dict[Platform, PlatformSpec] = {
    Platform.INSTAGRAM: PlatformSpec(
        Platform.INSTAGRAM, "Instagram", ("instagram.com", "instagr.am")
    ),
    Platform.FACEBOOK: PlatformSpec(
        Platform.FACEBOOK, "Facebook", ("facebook.com", "fb.watch", "fb.com")
    ),
    Platform.YOUTUBE: PlatformSpec(
        Platform.YOUTUBE, "YouTube", ("youtube.com", "youtu.be", "youtube-nocookie.com")
    ),
    Platform.TIKTOK: PlatformSpec(Platform.TIKTOK, "TikTok", ("tiktok.com",)),
    Platform.KICK: PlatformSpec(Platform.KICK, "Kick", ("kick.com",)),
    Platform.TWITCH: PlatformSpec(Platform.TWITCH, "Twitch", ("twitch.tv",)),
    Platform.TWITTER: PlatformSpec(Platform.TWITTER, "X (Twitter)", ("twitter.com", "x.com")),
}

SUPPORTED_NAMES = ", ".join(spec.name for spec in PLATFORMS.values())


@dataclass(frozen=True, slots=True)
class ValidatedUrl:
    url: str
    platform: Platform
    hostname: str


def _host_matches(host: str, domain: str) -> bool:
    return host == domain or host.endswith(f".{domain}")


def detect_platform(hostname: str) -> Platform | None:
    host = hostname.lower().rstrip(".")
    for platform, spec in PLATFORMS.items():
        if any(_host_matches(host, domain) for domain in spec.hosts):
            return platform
    return None


def _invalid(message: str, code: str = "invalid_url") -> AppError:
    return AppError(code, message, status_code=422)


def _not_media(platform: Platform, hint: str) -> AppError:
    return AppError(
        "not_media",
        hint,
        status_code=422,
        platform=platform.value,
    )


def _looks_like_instagram(path: str) -> bool:
    return bool(re.match(r"^/(?:[a-z]{2}(?:-[a-z]{2})?/)?(?:p|reel|reels|tv|share)/", path, re.I))


def _looks_like_facebook(url) -> bool:
    host = (url.hostname or "").lower()
    if host.endswith("fb.watch"):
        return len(url.path.strip("/")) > 0
    return bool(
        re.match(
            r"^/(?:watch|reel|reels|videos|share/v|story\.php)(?:/|$)",
            url.path,
            re.I,
        )
    )


def _looks_like_youtube(url) -> bool:
    host = (url.hostname or "").lower()
    if host == "youtu.be" or host.endswith(".youtu.be"):
        return len(url.path.strip("/")) > 0
    if url.path.rstrip("/") == "/watch":
        return bool(url.query and re.search(r"(?:^|&)v=[^&]+", url.query))
    return bool(re.match(r"^/(?:shorts|live|embed|clip)/[^/]+", url.path, re.I))


def _looks_like_tiktok(url) -> bool:
    host = (url.hostname or "").lower()
    path = url.path or "/"
    if host in {"vm.tiktok.com", "vt.tiktok.com"}:
        return bool(path.strip("/"))
    # Photo posts are intentionally rejected: there is no video stream to save.
    return bool(
        re.match(
            r"^/(?:@[^/]+/video/[^/]+|t/[^/]+|v/[^/]+|embed/v2/[^/]+)",
            path,
            re.I,
        )
    )


def _looks_like_kick(url) -> bool:
    if "clip=" in url.query or "video=" in url.query:
        return True
    # Kick VODs and clips are commonly nested under the channel name, e.g.
    # https://kick.com/scriptedshedy/videos/<uuid>. Channel homepages are not.
    return bool(
        re.match(
            r"^/(?:[^/]+/(?:video|videos|clip|clips)|video|videos|clip|clips)/[^/]+",
            url.path,
            re.I,
        )
    )


def _looks_like_twitch(url) -> bool:
    host = (url.hostname or "").lower()
    if host == "clips.twitch.tv" or host.endswith(".clips.twitch.tv"):
        return len(url.path.strip("/")) > 0
    return bool(re.match(r"^/(?:videos/\d+|[^/]+/clip/[^/]+)", url.path, re.I))


def _looks_like_twitter(path: str) -> bool:
    return bool(re.match(r"^/(?:i/(?:web/)?status|[^/]+/status)/\d+", path, re.I))


_NOT_MEDIA_HINTS = {
    Platform.INSTAGRAM: "Use the direct link to a public Reel, feed video or IGTV post. Profile and story links are not supported.",
    Platform.FACEBOOK: "Use the direct link to a public Facebook video, reel or Watch page.",
    Platform.YOUTUBE: "Use a link to one video or Short. Channel and playlist pages are not supported.",
    Platform.TIKTOK: "Use a public TikTok video link or share link. Photo posts and profile links are not supported.",
    Platform.KICK: "Use a public Kick VOD or clip link. Live channel pages are not supported.",
    Platform.TWITCH: "Use a Twitch VOD or clip link. Live channel pages are not supported.",
    Platform.TWITTER: "Use a direct link to an individual X post that contains native video. t.co short links are not accepted.",
}


def validate_url(raw: str, expected_platform: Platform | None = None) -> ValidatedUrl:
    value = (raw or "").strip()
    if not value:
        raise _invalid("Paste a public video link first.", "empty_url")
    if len(value) > MAX_URL_LENGTH:
        raise _invalid("That link is too long.")
    if _CONTROL_OR_SPACE.search(value) or "\\" in value:
        raise _invalid("Remove spaces, line breaks or backslashes from the link and try again.")

    candidate = value
    if not re.match(r"^[a-z][a-z0-9+.-]*:", candidate, re.I):
        candidate = f"https://{candidate.lstrip('/')}"

    try:
        parsed = urlsplit(candidate)
    except ValueError:
        raise _invalid("That does not look like a complete web address.") from None

    if parsed.username is not None or parsed.password is not None:
        raise _invalid("Links containing sign-in details are not accepted.")

    if parsed.scheme.lower() not in {"http", "https"}:
        raise _invalid("Only public http or https links are supported.", "insecure_url")

    try:
        port = parsed.port
    except ValueError:
        raise _invalid("The link contains an invalid port.") from None

    if port not in (None, 443):
        raise _invalid("This link uses an unusual port. Paste the normal public page URL.")

    host = (parsed.hostname or "").lower().rstrip(".")
    if not host or not host.isascii():
        raise _invalid("That link does not contain a valid public hostname.")

    platform = detect_platform(host)
    if platform is None:
        raise AppError(
            "unsupported_platform",
            f"Clipwell supports public links from {SUPPORTED_NAMES}. This site is not supported.",
            status_code=422,
        )

    path = parsed.path or "/"
    if platform is Platform.INSTAGRAM:
        is_media = _looks_like_instagram(path)
    elif platform is Platform.FACEBOOK:
        is_media = _looks_like_facebook(parsed)
    elif platform is Platform.YOUTUBE:
        is_media = _looks_like_youtube(parsed)
    elif platform is Platform.TIKTOK:
        is_media = _looks_like_tiktok(parsed)
    elif platform is Platform.KICK:
        is_media = _looks_like_kick(parsed)
    elif platform is Platform.TWITCH:
        is_media = _looks_like_twitch(parsed)
    else:
        is_media = _looks_like_twitter(path)

    if not is_media:
        raise _not_media(platform, _NOT_MEDIA_HINTS[platform])

    # Normalize to HTTPS and drop the default port. The fragment is irrelevant to extraction.
    netloc = host
    normalized = urlunsplit(("https", netloc, path, parsed.query, ""))

    if expected_platform is not None and platform is not expected_platform:
        detected = PLATFORMS[platform].name
        expected = PLATFORMS[expected_platform].name
        raise AppError(
            "platform_mismatch",
            f"This is a {detected} link, but you are on the {expected} downloader.",
            status_code=422,
            platform=platform.value,
            normalized_url=normalized,
        )

    return ValidatedUrl(url=normalized, platform=platform, hostname=host)
