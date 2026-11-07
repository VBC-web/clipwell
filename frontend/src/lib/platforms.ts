export const PLATFORM_KEYS = [
  'instagram',
  'facebook',
  'youtube',
  'tiktok',
  'kick',
  'twitch',
  'twitter',
] as const;

export type PlatformKey = (typeof PLATFORM_KEYS)[number];

export interface PlatformDefinition {
  key: PlatformKey;
  name: string;
  shortName: string;
  slug: string;
  hostname: string;
  colorClass: string;
  inputPlaceholder: string;
  homeNote: string;
}

export const PLATFORMS: Record<PlatformKey, PlatformDefinition> = {
  instagram: {
    key: 'instagram',
    name: 'Instagram',
    shortName: 'Instagram',
    slug: 'instagram-video-downloader',
    hostname: 'instagram.com',
    colorClass: 'platform-color-instagram',
    inputPlaceholder: 'https://www.instagram.com/reel/…',
    homeNote: 'Reels, feed videos and IGTV posts',
  },
  facebook: {
    key: 'facebook',
    name: 'Facebook',
    shortName: 'Facebook',
    slug: 'facebook-video-downloader',
    hostname: 'facebook.com',
    colorClass: 'platform-color-facebook',
    inputPlaceholder: 'https://www.facebook.com/watch/?v=…',
    homeNote: 'Watch videos, reels and public posts',
  },
  youtube: {
    key: 'youtube',
    name: 'YouTube',
    shortName: 'YouTube',
    slug: 'youtube-video-downloader',
    hostname: 'youtube.com',
    colorClass: 'platform-color-youtube',
    inputPlaceholder: 'https://www.youtube.com/watch?v=…',
    homeNote: 'Standard videos, Shorts and live replays',
  },
  tiktok: {
    key: 'tiktok',
    name: 'TikTok',
    shortName: 'TikTok',
    slug: 'tiktok-video-downloader',
    hostname: 'tiktok.com',
    colorClass: 'platform-color-tiktok',
    inputPlaceholder: 'https://www.tiktok.com/@creator/video/…',
    homeNote: 'Public videos and short share links',
  },
  kick: {
    key: 'kick',
    name: 'Kick',
    shortName: 'Kick',
    slug: 'kick-video-downloader',
    hostname: 'kick.com',
    colorClass: 'platform-color-kick',
    inputPlaceholder: 'https://kick.com/channel?video=…',
    homeNote: 'Public VODs and clips',
  },
  twitch: {
    key: 'twitch',
    name: 'Twitch',
    shortName: 'Twitch',
    slug: 'twitch-video-downloader',
    hostname: 'twitch.tv',
    colorClass: 'platform-color-twitch',
    inputPlaceholder: 'https://www.twitch.tv/videos/…',
    homeNote: 'VODs, highlights and clips',
  },
  twitter: {
    key: 'twitter',
    name: 'X (Twitter)',
    shortName: 'X',
    slug: 'twitter-video-downloader',
    hostname: 'x.com',
    colorClass: 'platform-color-twitter',
    inputPlaceholder: 'https://x.com/username/status/…',
    homeNote: 'Public posts with native video',
  },
};

export const PLATFORM_HOSTS: Record<PlatformKey, string[]> = {
  instagram: ['instagram.com', 'instagr.am'],
  facebook: ['facebook.com', 'fb.watch', 'fb.com'],
  youtube: ['youtube.com', 'youtu.be', 'youtube-nocookie.com'],
  tiktok: ['tiktok.com'],
  kick: ['kick.com'],
  twitch: ['twitch.tv'],
  twitter: ['twitter.com', 'x.com'],
};

export interface UrlCheck {
  ok: boolean;
  normalized?: string;
  platform?: PlatformKey;
  error?: string;
  errorCode?: 'empty' | 'malformed' | 'unsupported' | 'insecure' | 'not-media';
}

const CONTROL_OR_SPACE = /[\u0000-\u0020\u007f]/;
const MAX_URL_LENGTH = 2048;

function isAllowedHost(hostname: string, platform: PlatformKey): boolean {
  const host = hostname.toLowerCase().replace(/\.$/, '');
  return PLATFORM_HOSTS[platform].some(
    (domain) => host === domain || host.endsWith(`.${domain}`),
  );
}

export function detectPlatformFromHost(hostname: string): PlatformKey | null {
  for (const key of PLATFORM_KEYS) {
    if (isAllowedHost(hostname, key)) return key;
  }
  return null;
}

export function normalizeUrlInput(raw: string): UrlCheck {
  const value = raw.trim();

  if (!value) {
    return { ok: false, error: 'Paste a public video link first.', errorCode: 'empty' };
  }

  if (value.length > MAX_URL_LENGTH) {
    return { ok: false, error: 'That link is too long.', errorCode: 'malformed' };
  }

  if (CONTROL_OR_SPACE.test(value)) {
    return {
      ok: false,
      error: 'Remove spaces or line breaks from the link and try again.',
      errorCode: 'malformed',
    };
  }

  let candidate = value;
  if (!/^[a-z][a-z\d+.-]*:/i.test(candidate)) {
    candidate = `https://${candidate.replace(/^\/\//, '')}`;
  }

  let parsed: URL;
  try {
    parsed = new URL(candidate);
  } catch {
    return {
      ok: false,
      error: 'That does not look like a complete web address.',
      errorCode: 'malformed',
    };
  }

  if (parsed.username || parsed.password) {
    return {
      ok: false,
      error: 'Links containing sign-in details are not accepted.',
      errorCode: 'malformed',
    };
  }

  if (parsed.protocol !== 'https:' && parsed.protocol !== 'http:') {
    return {
      ok: false,
      error: 'Only public http or https links are supported.',
      errorCode: 'insecure',
    };
  }

  // Upgrading http keeps the request in transit encrypted without changing the content.
  parsed.protocol = 'https:';

  if (parsed.port && parsed.port !== '443') {
    return {
      ok: false,
      error: 'This link uses an unusual port. Paste the normal public page URL.',
      errorCode: 'malformed',
    };
  }

  parsed.hash = '';

  const platform = detectPlatformFromHost(parsed.hostname);
  if (!platform) {
    return {
      ok: false,
      error:
        'Clipwell supports public links from Instagram, Facebook, YouTube, TikTok, Kick, Twitch and X. This site is not supported.',
      errorCode: 'unsupported',
    };
  }

  return { ok: true, normalized: parsed.toString(), platform };
}

function looksLikeInstagram(path: string): boolean {
  return /^\/(?:[a-z]{2}\/)?(?:p|reel|reels|tv|share)\//i.test(path);
}

function looksLikeFacebook(url: URL): boolean {
  const host = url.hostname.toLowerCase();
  if (host.endsWith('fb.watch')) return url.pathname.length > 1;
  return /^\/(?:watch|reel|reels|videos|share\/v|story\.php)/i.test(url.pathname);
}

function looksLikeYouTube(url: URL): boolean {
  const host = url.hostname.toLowerCase();
  if (host === 'youtu.be' || host.endsWith('.youtu.be')) {
    return url.pathname.split('/').filter(Boolean).length > 0;
  }
  if (url.pathname === '/watch') {
    return Boolean(url.searchParams.get('v'));
  }
  return /^\/(?:shorts|live|embed|clip)\/[^/]+/i.test(url.pathname);
}

function looksLikeTikTok(url: URL): boolean {
  const host = url.hostname.toLowerCase();
  if (host === 'vm.tiktok.com' || host === 'vt.tiktok.com') {
    return url.pathname.length > 1;
  }
  // Photo posts are intentionally rejected: there is no video stream to save.
  return /^\/(?:@[^/]+\/video\/[^/]+|t\/[^/]+|v\/[^/]+|embed\/v2\/[^/]+)/i.test(url.pathname);
}

function looksLikeKick(url: URL): boolean {
  if (url.searchParams.has('clip') || url.searchParams.has('video')) return true;
  return /^\/(?:video|videos|clip|clips)\/[^/]+/i.test(url.pathname);
}

function looksLikeTwitch(url: URL): boolean {
  const host = url.hostname.toLowerCase();
  if (host === 'clips.twitch.tv' || host.endsWith('.clips.twitch.tv')) {
    return url.pathname.length > 1;
  }
  return /^\/(?:videos\/\d+|[^/]+\/clip\/[^/]+)/i.test(url.pathname);
}

function looksLikeTwitter(path: string): boolean {
  return /^\/(?:i\/)?(?:web\/)?status\/\d+/i.test(path) || /^\/i\/web\/status\/\d+/i.test(path);
}

/**
 * Checks that a URL is a public page URL for the expected platform and appears
 * to point at a video rather than a profile, playlist or live channel.
 */
export function validateContentUrl(
  raw: string,
  expectedPlatform?: PlatformKey,
): UrlCheck {
  const check = normalizeUrlInput(raw);
  if (!check.ok || !check.normalized || !check.platform) return check;

  const url = new URL(check.normalized);
  let isMediaCandidate = true;
  let hint = '';

  switch (check.platform) {
    case 'instagram':
      isMediaCandidate = looksLikeInstagram(url.pathname);
      hint = 'Use the direct link to a public Reel, feed video or IGTV post. Profile and story links are not supported.';
      break;
    case 'facebook':
      isMediaCandidate = looksLikeFacebook(url);
      hint = 'Use the direct link to a public Facebook video, reel or Watch page.';
      break;
    case 'youtube':
      isMediaCandidate = looksLikeYouTube(url);
      hint = 'Use a link to one video or Short. Channel and playlist pages are handled one video at a time.';
      break;
    case 'tiktok':
      isMediaCandidate = looksLikeTikTok(url);
      hint = 'Use a public TikTok video link or share link. Photo posts and profile links are not supported.';
      break;
    case 'kick':
      isMediaCandidate = looksLikeKick(url);
      hint = 'Use a public Kick VOD or clip link. Live channel pages are not supported.';
      break;
    case 'twitch':
      isMediaCandidate = looksLikeTwitch(url);
      hint = 'Use a Twitch VOD or clip link. Live channel pages are not supported.';
      break;
    case 'twitter':
      isMediaCandidate = looksLikeTwitter(url.pathname);
      hint = 'Use a direct link to an individual X post that contains native video.';
      break;
  }

  if (!isMediaCandidate) {
    return {
      ok: false,
      error: hint,
      errorCode: 'not-media',
      platform: check.platform,
      normalized: check.normalized,
    };
  }

  if (expectedPlatform && check.platform !== expectedPlatform) {
    const detected = PLATFORMS[check.platform].name;
    const expected = PLATFORMS[expectedPlatform].name;
    return {
      ok: false,
      error: `This is a ${detected} link, but you are on the ${expected} downloader.`,
      errorCode: 'unsupported',
      platform: check.platform,
      normalized: check.normalized,
    };
  }

  return check;
}

export function platformPath(key: PlatformKey): string {
  return `/${PLATFORMS[key].slug}/`;
}

export function platformPathWithUrl(key: PlatformKey, url: string): string {
  return `${platformPath(key)}?url=${encodeURIComponent(url)}`;
}

export function isPlatformKey(value: string): value is PlatformKey {
  return (PLATFORM_KEYS as readonly string[]).includes(value);
}

/** Pulls the first web URL out of a share message, or returns trimmed text. */
export function extractUrlFromText(text: string): string {
  const match = text.match(/https?:\/\/[^\s<>"']+/i);
  if (match) return match[0].replace(/[),.;!?]+$/g, '');
  return text.trim();
}

export function relatedPlatforms(key: PlatformKey, count = 4): PlatformDefinition[] {
  const index = PLATFORM_KEYS.indexOf(key);
  return Array.from({ length: count }, (_, offset) => {
    const next = PLATFORM_KEYS[(index + offset + 1) % PLATFORM_KEYS.length];
    return PLATFORMS[next];
  });
}
