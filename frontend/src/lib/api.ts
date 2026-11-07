export type PlatformKey =
  | 'instagram'
  | 'facebook'
  | 'youtube'
  | 'tiktok'
  | 'kick'
  | 'twitch'
  | 'twitter';

export interface FormatOption {
  id: string;
  label: string;
  ext: string;
  filesizeBytes: number | null;
  note: string | null;
}

export interface VideoOption extends FormatOption {
  height: number | null;
  fps: number | null;
  isOriginal: boolean;
}

export interface AudioOption extends FormatOption {
  bitrateKbps: number | null;
}

export interface CaptionTrack {
  lang: string;
  label: string;
  auto: boolean;
}

export interface MediaInfo {
  mediaId: string;
  platform: PlatformKey;
  sourceUrl: string;
  title: string;
  description: string | null;
  uploader: string | null;
  durationSeconds: number | null;
  thumbnailUrl: string | null;
  isLive: boolean;
  videoOptions: VideoOption[];
  audioOptions: AudioOption[];
  captions: CaptionTrack[];
  expiresInSeconds: number;
}

export interface DownloadJob {
  jobId: string;
  status: 'queued' | 'downloading' | 'processing' | 'ready' | 'error' | 'expired';
  progress: number;
  stage: string;
  message: string | null;
  error: string | null;
  filename: string | null;
  sizeBytes: number | null;
  downloadUrl: string | null;
  expiresAt: string | null;
}

export interface CaptionContent {
  lang: string;
  label: string;
  auto: boolean;
  text: string;
  srt: string;
}

interface ErrorEnvelope {
  error?: {
    code?: string;
    message?: string;
    retryAfterSeconds?: number;
  };
}

export class ApiError extends Error {
  code: string;
  status: number;
  retryAfterSeconds?: number;

  constructor(message: string, options: { code?: string; status?: number; retryAfterSeconds?: number } = {}) {
    super(message);
    this.name = 'ApiError';
    this.code = options.code || 'request_failed';
    this.status = options.status || 0;
    this.retryAfterSeconds = options.retryAfterSeconds;
  }
}

// An explicitly empty PUBLIC_API_BASE_URL means "same origin", which is what the
// bundled Nginx deployment uses to proxy /api to the backend.
const rawBase = import.meta.env.PUBLIC_API_BASE_URL;
const configuredBase = (
  rawBase === undefined ? 'http://127.0.0.1:8000' : rawBase
).replace(/\/+$/, '');

export const API_BASE = configuredBase;

export function apiUrl(path: string): string {
  return `${API_BASE}${path.startsWith('/') ? path : `/${path}`}`;
}

async function request<T>(
  path: string,
  options: RequestInit & { timeoutMs?: number } = {},
): Promise<T> {
  const { timeoutMs = 15_000, ...init } = options;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(apiUrl(path), {
      ...init,
      signal: controller.signal,
      headers: {
        Accept: 'application/json',
        ...(init.body ? { 'Content-Type': 'application/json' } : {}),
        ...init.headers,
      },
    });

    if (!response.ok) {
      let payload: ErrorEnvelope | null = null;
      try {
        payload = (await response.json()) as ErrorEnvelope;
      } catch {
        // A proxy or network layer may return HTML. Use a safe fallback below.
      }

      throw new ApiError(
        payload?.error?.message ||
          (response.status === 429
            ? 'Too many requests. Give it a minute and try again.'
            : 'The downloader could not complete that request.'),
        {
          code: payload?.error?.code || `http_${response.status}`,
          status: response.status,
          retryAfterSeconds: payload?.error?.retryAfterSeconds,
        },
      );
    }

    return (await response.json()) as T;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new ApiError('The request took too long. The platform may be slow or unavailable.', {
        code: 'timeout',
      });
    }
    throw new ApiError(
      'Could not reach the Clipwell API. The backend may be offline or blocked by your network.',
      { code: 'network_error' },
    );
  } finally {
    clearTimeout(timer);
  }
}

export function extractMedia(url: string): Promise<MediaInfo> {
  return request<MediaInfo>('/api/extract', {
    method: 'POST',
    body: JSON.stringify({ url }),
    timeoutMs: 75_000,
  });
}

export function createDownload(mediaId: string, optionId: string): Promise<DownloadJob> {
  return request<DownloadJob>('/api/download', {
    method: 'POST',
    body: JSON.stringify({ mediaId, optionId }),
    timeoutMs: 20_000,
  });
}

export function getJob(jobId: string): Promise<DownloadJob> {
  return request<DownloadJob>(`/api/jobs/${encodeURIComponent(jobId)}`, {
    timeoutMs: 12_000,
  });
}

export function fetchCaptions(
  mediaId: string,
  lang: string,
  auto: boolean,
): Promise<CaptionContent> {
  return request<CaptionContent>(`/api/media/${encodeURIComponent(mediaId)}/captions`, {
    method: 'POST',
    body: JSON.stringify({ lang, auto }),
    timeoutMs: 90_000,
  });
}

export function formatBytes(bytes: number | null | undefined): string {
  if (!bytes || bytes <= 0) return '';
  const units = ['B', 'KB', 'MB', 'GB'];
  const exponent = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  const value = bytes / 1024 ** exponent;
  return `${value >= 100 || exponent === 0 ? value.toFixed(0) : value.toFixed(1)} ${units[exponent]}`;
}

export function formatDuration(seconds: number | null | undefined): string {
  if (seconds === null || seconds === undefined || !Number.isFinite(seconds) || seconds <= 0) {
    return '';
  }
  const total = Math.round(seconds);
  const hours = Math.floor(total / 3600);
  const minutes = Math.floor((total % 3600) / 60);
  const secs = total % 60;
  if (hours > 0) {
    return `${hours}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  }
  return `${minutes}:${String(secs).padStart(2, '0')}`;
}
