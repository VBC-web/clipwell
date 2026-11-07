import {
  Captions,
  Download,
  Film,
  LoaderCircle,
  Music2,
  ShieldCheck,
} from 'lucide-react';
import type { AudioOption, DownloadJob, MediaInfo, VideoOption } from '../../lib/api';
import { formatBytes } from '../../lib/api';
import { CaptionPanel } from './CaptionPanel';
import { DownloadProgress } from './DownloadProgress';

export type DownloadTab = 'video' | 'audio' | 'captions';

interface Props {
  media: MediaInfo;
  tab: DownloadTab;
  onTabChange: (tab: DownloadTab) => void;
  videoId: string | null;
  audioId: string | null;
  onVideoChange: (id: string) => void;
  onAudioChange: (id: string) => void;
  job: DownloadJob | null;
  starting: boolean;
  onDownload: () => void;
  onRetry: () => void;
}

function VideoChoice({
  option,
  checked,
  name,
  onChange,
}: {
  option: VideoOption;
  checked: boolean;
  name: string;
  onChange: () => void;
}) {
  return (
    <label
      className={`relative flex cursor-pointer flex-col rounded-md border p-3 transition-colors ${
        checked
          ? 'border-accent bg-accent-soft/70'
          : 'border-line bg-surface hover:border-line-strong hover:bg-sunken/40'
      }`}
    >
      <input
        type="radio"
        name={name}
        value={option.id}
        checked={checked}
        onChange={onChange}
        className="sr-only"
      />
      <span className="flex items-start justify-between gap-2">
        <span className="text-sm font-[720] text-ink">{option.label}</span>
        <span
          className={`mt-0.5 grid h-3.5 w-3.5 flex-none place-items-center rounded-full border ${
            checked ? 'border-accent bg-accent' : 'border-line-strong bg-surface'
          }`}
          aria-hidden="true"
        >
          {checked && <span className="h-1.5 w-1.5 rounded-full bg-white" />}
        </span>
      </span>
      <span className="mt-1 flex flex-wrap items-center gap-1.5 text-[0.7rem] text-muted">
        <span className="tag !px-1.5 !py-0">{option.ext.toUpperCase()}</span>
        {option.isOriginal && <span className="tag tag-accent !px-1.5 !py-0">Original</span>}
        {option.note && <span>{option.note}</span>}
      </span>
      <span className="mt-2 text-[0.68rem] text-muted">
        {option.filesizeBytes ? `About ${formatBytes(option.filesizeBytes)}` : 'Size reported after download'}
      </span>
    </label>
  );
}

function AudioChoice({
  option,
  checked,
  name,
  onChange,
}: {
  option: AudioOption;
  checked: boolean;
  name: string;
  onChange: () => void;
}) {
  return (
    <label
      className={`relative flex cursor-pointer items-start gap-3 rounded-md border p-3 transition-colors ${
        checked
          ? 'border-accent bg-accent-soft/70'
          : 'border-line bg-surface hover:border-line-strong hover:bg-sunken/40'
      }`}
    >
      <input
        type="radio"
        name={name}
        value={option.id}
        checked={checked}
        onChange={onChange}
        className="mt-1 h-3.5 w-3.5 accent-[var(--accent)]"
      />
      <span className="min-w-0 flex-1">
        <span className="flex flex-wrap items-center gap-2">
          <span className="text-sm font-[720] text-ink">{option.label}</span>
          <span className="tag !px-1.5 !py-0">{option.ext.toUpperCase()}</span>
        </span>
        <span className="mt-1 block text-[0.72rem] text-muted">
          {[option.bitrateKbps ? `${option.bitrateKbps} kbps` : null, option.note]
            .filter(Boolean)
            .join(' · ') || 'Audio-only export'}
        </span>
        <span className="mt-1 block text-[0.68rem] text-muted">
          {option.filesizeBytes ? `About ${formatBytes(option.filesizeBytes)}` : 'Size reported after download'}
        </span>
      </span>
    </label>
  );
}

export function DownloadPanel({
  media,
  tab,
  onTabChange,
  videoId,
  audioId,
  onVideoChange,
  onAudioChange,
  job,
  starting,
  onDownload,
  onRetry,
}: Props) {
  const video = media.videoOptions.find((option) => option.id === videoId);
  const audio = media.audioOptions.find((option) => option.id === audioId);
  const selected = tab === 'video' ? video : tab === 'audio' ? audio : null;
  const pending = job && ['queued', 'downloading', 'processing'].includes(job.status);
  const ready = job?.status === 'ready';
  const buttonDisabled =
    tab === 'captions' || !selected || starting || Boolean(pending) || Boolean(ready);

  const tabItems: { key: DownloadTab; label: string; icon: typeof Film; count: number }[] = [
    { key: 'video', label: 'Video', icon: Film, count: media.videoOptions.length },
    { key: 'audio', label: 'Audio', icon: Music2, count: media.audioOptions.length },
    { key: 'captions', label: 'Captions', icon: Captions, count: media.captions.length },
  ];

  const buttonLabel = starting
    ? 'Starting download…'
    : pending
      ? 'Download in progress…'
      : ready
        ? 'Download complete'
        : tab === 'audio' && audio
          ? `Download ${audio.ext.toUpperCase()}`
          : video
            ? `Download MP4 · ${video.label}`
            : 'Choose a format';

  return (
    <section className="card mt-6 overflow-hidden animate-rise" aria-labelledby="format-heading">
      <div className="border-b border-line px-4 pt-4 md:px-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 id="format-heading" className="font-sans text-base font-[750] tracking-[-0.01em] text-ink">
              Choose a download
            </h2>
            <p className="mt-0.5 text-xs text-muted">
              Only formats returned for this post are shown.
            </p>
          </div>
          <span className="tag">
            <ShieldCheck className="h-3 w-3" aria-hidden="true" />
            Public source
          </span>
        </div>

        <div className="mt-4 flex gap-1 overflow-x-auto" role="group" aria-label="Download type">
          {tabItems.map((item) => {
            const Icon = item.icon;
            const active = tab === item.key;
            return (
              <button
                key={item.key}
                type="button"
                onClick={() => onTabChange(item.key)}
                aria-pressed={active}
                className={`inline-flex items-center gap-1.5 border-b-2 px-3 py-2.5 text-[0.8rem] font-[680] transition-colors ${
                  active
                    ? 'border-accent text-accent-ink'
                    : 'border-transparent text-muted hover:text-ink'
                }`}
              >
                <Icon className="h-3.5 w-3.5" aria-hidden="true" />
                {item.label}
                <span className={`text-[0.66rem] ${active ? 'text-accent' : 'text-muted'}`}>
                  {item.count}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      <div className="p-4 md:p-5">
        {tab === 'video' && (
          <div>
            {media.videoOptions.length > 0 ? (
              <fieldset>
                <legend className="mb-3 text-xs text-muted">
                  Video downloads are prepared as MP4 files. Pick a resolution from the source.
                </legend>
                <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                  {media.videoOptions.map((option) => (
                    <VideoChoice
                      key={option.id}
                      option={option}
                      checked={option.id === videoId}
                      name={`video-format-${media.mediaId}`}
                      onChange={() => onVideoChange(option.id)}
                    />
                  ))}
                </div>
              </fieldset>
            ) : (
              <div className="rounded-md border border-line bg-sunken/50 p-5 text-center">
                <Film className="mx-auto h-5 w-5 text-muted" aria-hidden="true" />
                <p className="mt-2 text-sm font-[650] text-ink">No video format was returned</p>
                <p className="mx-auto mt-1 max-w-md text-xs leading-relaxed text-muted">
                  The post was read successfully, but the platform did not expose a downloadable
                  video stream. There is nothing to save as a video right now.
                </p>
              </div>
            )}
          </div>
        )}

        {tab === 'audio' && (
          <div>
            {media.audioOptions.length > 0 ? (
              <fieldset>
                <legend className="mb-3 text-xs text-muted">
                  Audio-only files are generated from the source audio stream when available.
                </legend>
                <div className="grid gap-2 sm:grid-cols-2">
                  {media.audioOptions.map((option) => (
                    <AudioChoice
                      key={option.id}
                      option={option}
                      checked={option.id === audioId}
                      name={`audio-format-${media.mediaId}`}
                      onChange={() => onAudioChange(option.id)}
                    />
                  ))}
                </div>
              </fieldset>
            ) : (
              <div className="rounded-md border border-line bg-sunken/50 p-5 text-center">
                <Music2 className="mx-auto h-5 w-5 text-muted" aria-hidden="true" />
                <p className="mt-2 text-sm font-[650] text-ink">No separate audio stream is available</p>
                <p className="mx-auto mt-1 max-w-md text-xs leading-relaxed text-muted">
                  The video may still contain audio, but the platform did not expose a standalone
                  audio track that Clipwell can convert honestly.
                </p>
              </div>
            )}
          </div>
        )}

        {tab === 'captions' && <CaptionPanel media={media} />}

        {tab !== 'captions' && (
          <div className="mt-4 flex flex-col gap-3 border-t border-line pt-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="text-xs text-muted">
              {selected ? (
                <>
                  Selected: <span className="font-[650] text-ink">{selected.label}</span>
                  {selected.filesizeBytes ? ` · about ${formatBytes(selected.filesizeBytes)}` : ''}
                </>
              ) : (
                'Choose an available format to continue.'
              )}
            </div>
            <button
              type="button"
              className="btn btn-primary min-w-[12rem]"
              onClick={onDownload}
              disabled={buttonDisabled}
            >
              {starting || pending ? (
                <LoaderCircle className="h-4 w-4 animate-spin" aria-hidden="true" />
              ) : (
                <Download className="h-4 w-4" aria-hidden="true" />
              )}
              {buttonLabel}
            </button>
          </div>
        )}

        {job && <DownloadProgress job={job} onRetry={onRetry} />}
      </div>
    </section>
  );
}
