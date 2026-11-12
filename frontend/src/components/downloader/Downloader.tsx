import {
  useCallback,
  useEffect,
  useId,
  useMemo,
  useRef,
  useState,
} from 'react';
import {
  AlertCircle,
  ArrowRight,
  Clipboard,
  Download,
  LoaderCircle,
  LockKeyhole,
  ShieldCheck,
  TimerReset,
} from 'lucide-react';
import {
  ApiError,
  apiUrl,
  createDownload,
  extractMedia,
  getJob,
  type DownloadJob,
  type MediaInfo,
} from '../../lib/api';
import {
  PLATFORM_KEYS,
  PLATFORMS,
  extractUrlFromText,
  normalizeUrlInput,
  platformPath,
  platformPathWithUrl,
  validateContentUrl,
  type PlatformKey,
} from '../../lib/platforms';
import { DownloadPanel, type DownloadTab } from './DownloadPanel';
import { MediaDetails } from './MediaDetails';
import { PlatformMark } from './PlatformMark';
import { Toast, type ToastTone } from './Toast';

interface Props {
  platform?: PlatformKey;
  initialUrl?: string;
  className?: string;
}

interface UiError {
  message: string;
  code: string;
}

interface Mismatch {
  platform: PlatformKey;
  url: string;
}

interface ToastState {
  message: string;
  tone: ToastTone;
}

function errorMessage(error: unknown): string {
  if (error instanceof ApiError || error instanceof Error) return error.message;
  return 'Something went wrong while processing this link.';
}

export default function Downloader({ platform, initialUrl = '', className = '' }: Props) {
  const inputId = useId();
  const helperId = `${inputId}-helper`;
  const inputRef = useRef<HTMLInputElement>(null);
  const resultRef = useRef<HTMLDivElement>(null);
  const booted = useRef(false);
  const autoSavedJob = useRef<string | null>(null);

  const [url, setUrl] = useState(initialUrl);
  const [touched, setTouched] = useState(false);
  const [busy, setBusy] = useState(false);
  const [media, setMedia] = useState<MediaInfo | null>(null);
  const [uiError, setUiError] = useState<UiError | null>(null);
  const [mismatch, setMismatch] = useState<Mismatch | null>(null);
  const [redirecting, setRedirecting] = useState<PlatformKey | null>(null);
  const [pasteHint, setPasteHint] = useState<string | null>(null);
  const [tab, setTab] = useState<DownloadTab>('video');
  const [videoId, setVideoId] = useState<string | null>(null);
  const [audioId, setAudioId] = useState<string | null>(null);
  const [job, setJob] = useState<DownloadJob | null>(null);
  const [starting, setStarting] = useState(false);
  const [toast, setToast] = useState<ToastState | null>(null);

  const platformDefinition = platform ? PLATFORMS[platform] : null;
  const isHome = !platform;
  const detection = useMemo(() => {
    if (!url.trim()) return null;
    return normalizeUrlInput(url);
  }, [url]);
  const detectedPlatform = detection?.ok ? detection.platform : null;
  const detectionMismatch = Boolean(
    detectedPlatform && platform && detectedPlatform !== platform,
  );

  const pendingJob = Boolean(
    job && ['queued', 'downloading', 'processing'].includes(job.status),
  );

  const showToast = useCallback((message: string, tone: ToastTone = 'info') => {
    setToast({ message, tone });
  }, []);

  useEffect(() => {
    if (!toast) return;
    const timer = window.setTimeout(() => setToast(null), 4600);
    return () => window.clearTimeout(timer);
  }, [toast]);

  const submit = useCallback(
    async (rawUrl: string) => {
      setTouched(true);
      setUiError(null);
      setMismatch(null);
      setRedirecting(null);
      setPasteHint(null);

      const check = validateContentUrl(rawUrl, platform);

      if (!check.ok) {
        if (check.platform && platform && check.platform !== platform && check.normalized) {
          setMismatch({ platform: check.platform, url: check.normalized });
        }
        setUiError({
          message: check.error || 'That link could not be validated.',
          code: check.errorCode || 'invalid_url',
        });
        return;
      }

      if (!check.normalized || !check.platform) {
        setUiError({ message: 'That link could not be validated.', code: 'invalid_url' });
        return;
      }

      if (isHome) {
        setRedirecting(check.platform);
        window.location.assign(platformPathWithUrl(check.platform, check.normalized));
        return;
      }

      setBusy(true);
      setMedia(null);
      setJob(null);
      setVideoId(null);
      setAudioId(null);
      setUrl(check.normalized);

      try {
        const result = await extractMedia(check.normalized);
        if (result.platform !== platform) {
          throw new ApiError(
            'The link resolved to a different platform than this page handles. Open the matching downloader and try again.',
            { code: 'platform_mismatch' },
          );
        }

        setMedia(result);
        setVideoId(result.videoOptions[0]?.id ?? null);
        setAudioId(result.audioOptions[0]?.id ?? null);
        setTab(
          result.videoOptions.length > 0
            ? 'video'
            : result.audioOptions.length > 0
              ? 'audio'
              : 'video',
        );

        window.requestAnimationFrame(() => {
          const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
          resultRef.current?.scrollIntoView({
            behavior: reduceMotion ? 'auto' : 'smooth',
            block: 'start',
          });
        });
      } catch (error) {
        setUiError({
          message: errorMessage(error),
          code: error instanceof ApiError ? error.code : 'extract_failed',
        });
      } finally {
        setBusy(false);
      }
    },
    [isHome, platform],
  );

  useEffect(() => {
    if (booted.current) return;
    booted.current = true;

    const queryUrl = initialUrl || new URLSearchParams(window.location.search).get('url') || '';
    if (!queryUrl) return;

    setUrl(queryUrl);
    void submit(queryUrl);
  }, [initialUrl, submit]);

  // Poll the job until it reaches a terminal state. Each update reschedules.
  useEffect(() => {
    if (!job) return;
    if (['ready', 'error', 'expired'].includes(job.status)) return;

    let cancelled = false;
    const timer = window.setTimeout(async () => {
      try {
        const next = await getJob(job.jobId);
        if (!cancelled) setJob(next);
      } catch (error) {
        if (!cancelled) {
          setJob({
            ...job,
            status: 'error',
            error: errorMessage(error),
            stage: 'The download could not be completed',
          });
        }
      }
    }, 900);

    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [job]);

  // Trigger the browser download once, while keeping the visible save button as a fallback.
  useEffect(() => {
    if (job?.status !== 'ready' || !job.downloadUrl || autoSavedJob.current === job.jobId) return;

    autoSavedJob.current = job.jobId;
    const anchor = document.createElement('a');
    anchor.href = apiUrl(job.downloadUrl);
    if (job.filename) anchor.download = job.filename;
    anchor.rel = 'noopener';
    anchor.style.display = 'none';
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    showToast('Your file is ready. Temporary storage is cleaned automatically.', 'success');
  }, [job, showToast]);

  function handleSubmit(event: { preventDefault: () => void }) {
    event.preventDefault();
    if (busy) return;
    void submit(url);
  }

  async function handlePaste() {
    setPasteHint(null);
    try {
      if (!navigator.clipboard?.readText) {
        throw new Error('Clipboard API unavailable');
      }
      const clipboard = await navigator.clipboard.readText();
      if (!clipboard.trim()) {
        showToast('Your clipboard is empty.', 'info');
        inputRef.current?.focus();
        return;
      }
      const nextUrl = extractUrlFromText(clipboard);
      setUrl(nextUrl);
      setTouched(false);
      setUiError(null);
      setRedirecting(null);

      const check = validateContentUrl(nextUrl);
      if (platform && check.ok && check.platform && check.platform !== platform && check.normalized) {
        setMismatch({ platform: check.platform, url: check.normalized });
      } else {
        setMismatch(null);
      }

      inputRef.current?.focus();
    } catch {
      setPasteHint(
        'Clipboard access was blocked by your browser. Select the field and paste with Ctrl+V or ⌘V.',
      );
      inputRef.current?.focus();
    }
  }

  function handleUrlChange(value: string) {
    setUrl(value);
    setMismatch(null);
    setUiError(null);
    setPasteHint(null);
    setRedirecting(null);
  }

  function handleVideoChange(id: string) {
    if (pendingJob) return;
    setVideoId(id);
    setJob(null);
  }

  function handleAudioChange(id: string) {
    if (pendingJob) return;
    setAudioId(id);
    setJob(null);
  }

  function handleTabChange(nextTab: DownloadTab) {
    setTab(nextTab);
  }

  async function handleDownload() {
    if (!media || starting || pendingJob) return;
    const optionId = tab === 'video' ? videoId : tab === 'audio' ? audioId : null;
    if (!optionId) return;

    setStarting(true);
    setJob(null);
    setToast(null);

    try {
      const created = await createDownload(media.mediaId, optionId);
      setJob(created);
      showToast('Download queued. This can take a moment for larger files.', 'info');
    } catch (error) {
      setToast({ message: errorMessage(error), tone: 'error' });
    } finally {
      setStarting(false);
    }
  }

  const helperText = (() => {
    if (pasteHint) return pasteHint;
    if (detection?.ok && detection.platform) {
      if (detectionMismatch) {
        return `Detected ${PLATFORMS[detection.platform].name}. This is the ${platformDefinition?.name} downloader.`;
      }
      return `Detected ${PLATFORMS[detection.platform].name}. The link looks valid.`;
    }
    if (touched && detection && !detection.ok && detection.errorCode !== 'empty') {
      return detection.error || 'Check the link and try again.';
    }
    if (platformDefinition) {
      return `Paste a direct link to a public ${platformDefinition.name} video, clip or VOD.`;
    }
    return 'Paste a link and Clipwell will send you to the right platform downloader.';
  })();

  const helperIsWarning = Boolean(
    pasteHint || detectionMismatch || (touched && detection && !detection.ok),
  );

  const inputPlaceholder =
    platformDefinition?.inputPlaceholder || 'Paste a public video link from any supported platform';

  return (
    <div id="downloader" className={`scroll-mt-24 ${className}`}>
      <div className="card card-elevated overflow-hidden">
        <div className="border-b border-line px-4 py-4 md:px-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="eyebrow">{isHome ? 'Universal downloader' : `${platformDefinition?.name} downloader`}</p>
              <h2 className="mt-2 text-[1.45rem] leading-tight md:text-[1.65rem]">
                {isHome
                  ? 'Paste a public video link'
                  : `Paste a public ${platformDefinition?.name} link`}
              </h2>
            </div>
            <span className="tag tag-accent">
              {isHome ? 'Auto-detect' : 'Validated link'}
            </span>
          </div>
        </div>

        <div className="p-4 md:p-6">
          <form onSubmit={handleSubmit} noValidate>
            <label htmlFor={inputId} className="field-label">
              Video URL
            </label>
            <div className="flex flex-col gap-2 sm:flex-row">
              <div className="relative min-w-0 flex-1">
                <svg
                  className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.8"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  aria-hidden="true"
                >
                  <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" />
                  <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" />
                </svg>
                <input
                  ref={inputRef}
                  id={inputId}
                  name="url"
                  type="url"
                  inputMode="url"
                  autoComplete="off"
                  autoCapitalize="none"
                  spellCheck={false}
                  maxLength={2048}
                  className="text-input !h-[3.25rem] !pr-[5.2rem] !pl-10"
                  placeholder={inputPlaceholder}
                  value={url}
                  onChange={(event) => handleUrlChange(event.target.value)}
                  onBlur={() => setTouched(true)}
                  aria-invalid={Boolean(uiError)}
                  aria-describedby={helperId}
                />
                <button
                  type="button"
                  onClick={handlePaste}
                  className="btn btn-secondary btn-sm absolute right-1.5 top-1/2 -translate-y-1/2 !min-h-9"
                >
                  <Clipboard className="h-3.5 w-3.5" aria-hidden="true" />
                  Paste
                </button>
              </div>

              <button
                type="submit"
                className="btn btn-primary btn-lg shrink-0 sm:w-auto"
                disabled={busy || Boolean(redirecting) || !url.trim()}
              >
                {busy ? (
                  <LoaderCircle className="h-4 w-4 animate-spin" aria-hidden="true" />
                ) : (
                  <Download className="h-4 w-4" aria-hidden="true" />
                )}
                {busy ? 'Checking…' : 'Download'}
                {!busy && <ArrowRight className="h-4 w-4" aria-hidden="true" />}
              </button>
            </div>

            <p
              id={helperId}
              className={`mt-2 flex items-start gap-1.5 text-[0.72rem] leading-relaxed ${
                helperIsWarning ? 'text-warning' : 'text-muted'
              }`}
              aria-live="polite"
            >
              {detection?.ok ? (
                <span
                  className={`mt-1.5 h-1.5 w-1.5 flex-none rounded-full ${
                    detectionMismatch ? 'bg-warning' : 'bg-success'
                  }`}
                  aria-hidden="true"
                />
              ) : (
                <ShieldCheck className="mt-0.5 h-3.5 w-3.5 flex-none" aria-hidden="true" />
              )}
              <span>{helperText}</span>
            </p>

            <div className="mt-4">
              <p className="mb-2 text-[0.68rem] font-[720] uppercase tracking-[0.1em] text-muted">
                {isHome ? 'Choose a platform instead' : 'Switch platform'}
              </p>
              <div className="flex flex-wrap gap-1.5" aria-label="Supported platforms">
                {PLATFORM_KEYS.map((key) => {
                  const definition = PLATFORMS[key];
                  const href =
                    detection?.ok && detection.platform === key && detection.normalized
                      ? platformPathWithUrl(key, detection.normalized)
                      : platformPath(key);
                  const active = platform === key;

                  return (
                    <a
                      key={key}
                      href={href}
                      aria-current={active ? 'page' : undefined}
                      className={`inline-flex items-center gap-1.5 rounded-sm border px-2 py-1.5 text-[0.72rem] font-[650] no-underline transition-colors ${
                        active
                          ? 'border-accent bg-accent-soft text-accent-ink'
                          : 'border-line bg-surface text-soft hover:border-line-strong hover:bg-sunken hover:text-ink'
                      }`}
                      title={definition.name}
                    >
                      <PlatformMark platform={key} size="sm" className="!h-5 !w-5 !rounded-[0.25rem]" />
                      <span>{definition.shortName}</span>
                    </a>
                  );
                })}
              </div>
            </div>
          </form>

          <div className="mt-4 flex flex-wrap items-center gap-x-4 gap-y-2 border-t border-line pt-3 text-[0.68rem] text-muted">
            <span className="inline-flex items-center gap-1.5">
              <ShieldCheck className="h-3.5 w-3.5" aria-hidden="true" />
              Public links only
            </span>
            <span className="inline-flex items-center gap-1.5">
              <LockKeyhole className="h-3.5 w-3.5" aria-hidden="true" />
              No sign-in or DRM bypass
            </span>
            <span className="inline-flex items-center gap-1.5">
              <TimerReset className="h-3.5 w-3.5" aria-hidden="true" />
              Temporary files
            </span>
          </div>
        </div>
      </div>

      {mismatch && (
        <div className="notice mt-4 flex items-start gap-3 animate-fade" role="status">
          <PlatformMark platform={mismatch.platform} />
          <div className="min-w-0 flex-1">
            <p className="font-[700] text-ink">
              This is a {PLATFORMS[mismatch.platform].name} link
            </p>
            <p className="mt-1 text-xs leading-relaxed text-soft">
              You are on the {platformDefinition?.name} downloader. Open the matching downloader
              below and the link will be filled in for you.
            </p>
          </div>
          <a
            href={platformPathWithUrl(mismatch.platform, mismatch.url)}
            className="btn btn-primary btn-sm shrink-0"
          >
            Open {PLATFORMS[mismatch.platform].shortName}
            <ArrowRight className="h-3.5 w-3.5" aria-hidden="true" />
          </a>
        </div>
      )}

      {uiError && (
        <div
          className="mt-4 flex items-start gap-3 rounded-md border border-[color-mix(in_srgb,var(--danger)_28%,var(--line))] bg-danger-soft p-4 animate-fade"
          role="alert"
        >
          <AlertCircle className="mt-0.5 h-5 w-5 flex-none text-danger" aria-hidden="true" />
          <div className="min-w-0">
            <p className="text-sm font-[700] text-danger">That link needs another look</p>
            <p className="mt-1 text-xs leading-relaxed text-danger/90">{uiError.message}</p>
            {uiError.code === 'unsupported' && (
              <p className="mt-2 text-xs text-danger/80">
                Supported sites: Instagram, Facebook, YouTube, TikTok, Kick, Twitch and X.
              </p>
            )}
            <button
              type="button"
              className="mt-2 text-xs font-[650] text-danger underline decoration-danger/30 underline-offset-2 hover:decoration-danger"
              onClick={() =>
                window.dispatchEvent(
                  new CustomEvent('clipwell:open-feedback', {
                    detail: { url, error: uiError.message },
                  }),
                )
              }
            >
              Report this broken link
            </button>
          </div>
        </div>
      )}

      {redirecting && (
        <div className="notice mt-4 flex items-center gap-3 animate-fade" role="status">
          <LoaderCircle className="h-4 w-4 animate-spin text-accent" aria-hidden="true" />
          <span>
            Opening the {PLATFORMS[redirecting].name} downloader with your link…
          </span>
        </div>
      )}

      {busy && (
        <div className="card mt-6 p-5 animate-fade" aria-busy="true" aria-live="polite">
          <span className="sr-only">Reading the public link and available formats.</span>
          <div className="flex items-center gap-3">
            <LoaderCircle className="h-5 w-5 animate-spin text-accent" aria-hidden="true" />
            <div>
              <p className="text-sm font-[700] text-ink">Reading the public link</p>
              <p className="mt-0.5 text-xs text-muted">
                This can take a few seconds while the platform responds.
              </p>
            </div>
          </div>
          <div className="mt-5 grid gap-5 md:grid-cols-[17rem_1fr]">
            <div className="skeleton aspect-video rounded-md" />
            <div className="self-center space-y-3">
              <div className="skeleton h-5 w-4/5 rounded-sm" />
              <div className="skeleton h-3 w-2/5 rounded-sm" />
              <div className="skeleton h-3 w-3/5 rounded-sm" />
              <div className="flex gap-2 pt-2">
                <div className="skeleton h-7 w-20 rounded-full" />
                <div className="skeleton h-7 w-24 rounded-full" />
              </div>
            </div>
          </div>
        </div>
      )}

      {media && (
        <div ref={resultRef} className="scroll-mt-24 pt-8">
          <DownloadPanel
            media={media}
            tab={tab}
            onTabChange={handleTabChange}
            videoId={videoId}
            audioId={audioId}
            onVideoChange={handleVideoChange}
            onAudioChange={handleAudioChange}
            job={job}
            starting={starting}
            onDownload={handleDownload}
            onRetry={handleDownload}
          />
          <MediaDetails media={media} />
        </div>
      )}

      {toast && (
        <Toast
          message={toast.message}
          tone={toast.tone}
          onClose={() => setToast(null)}
        />
      )}
    </div>
  );
}
