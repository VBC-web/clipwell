import { useState } from 'react';
import {
  Clock3,
  ExternalLink,
  FileText,
  ImageOff,
  Link2,
  Play,
  UserRound,
} from 'lucide-react';
import type { MediaInfo } from '../../lib/api';
import { formatDuration } from '../../lib/api';
import { PLATFORMS } from '../../lib/platforms';
import { CopyButton } from './CopyButton';
import { PlatformMark } from './PlatformMark';

interface Props {
  media: MediaInfo;
}

export function MediaDetails({ media }: Props) {
  const [expanded, setExpanded] = useState(false);
  const [imageFailed, setImageFailed] = useState(false);
  const platform = PLATFORMS[media.platform];
  const duration = formatDuration(media.durationSeconds);
  const longDescription = Boolean(media.description && media.description.length > 420);

  return (
    <section aria-labelledby="media-title" className="animate-rise">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2 text-[0.72rem] font-[700] uppercase tracking-[0.08em] text-muted">
          <PlatformMark platform={media.platform} size="sm" />
          <span>{platform.name}</span>
          <span className="text-line-strong" aria-hidden="true">/</span>
          <span>Public media</span>
        </div>
        <a
          href={media.sourceUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="btn btn-ghost btn-sm text-[0.72rem]"
        >
          Open original
          <ExternalLink className="h-3.5 w-3.5" aria-hidden="true" />
        </a>
      </div>

      <div className="grid gap-5 md:grid-cols-[minmax(0,17rem)_minmax(0,1fr)] md:gap-6">
        <div className="relative aspect-video overflow-hidden rounded-md border border-line bg-sunken md:aspect-[4/3]">
          {media.thumbnailUrl && !imageFailed ? (
            <img
              src={media.thumbnailUrl}
              alt={`Thumbnail for ${media.title}`}
              className="h-full w-full object-cover"
              loading="lazy"
              decoding="async"
              referrerPolicy="no-referrer"
              onError={() => setImageFailed(true)}
            />
          ) : (
            <div className="grid h-full place-items-center px-6 text-center">
              <div>
                <ImageOff className="mx-auto h-6 w-6 text-muted" aria-hidden="true" />
                <p className="mt-2 text-xs text-muted">No thumbnail was provided for this post.</p>
              </div>
            </div>
          )}

          {duration && (
            <span className="absolute bottom-2 right-2 inline-flex items-center gap-1 rounded-xs bg-black/75 px-1.5 py-0.5 text-[0.68rem] font-[700] tabular-nums text-white">
              <Clock3 className="h-3 w-3" aria-hidden="true" />
              {duration}
            </span>
          )}
          <span className="absolute left-2 top-2 inline-flex items-center gap-1 rounded-xs bg-black/75 px-1.5 py-0.5 text-[0.62rem] font-[700] uppercase tracking-[0.06em] text-white">
            <Play className="h-3 w-3 fill-current" aria-hidden="true" />
            Video
          </span>
        </div>

        <div className="min-w-0 self-center">
          <div className="flex items-start gap-2">
            <h2 id="media-title" className="min-w-0 flex-1 text-[1.55rem] leading-[1.16] md:text-[1.85rem]">
              {media.title}
            </h2>
            <CopyButton
              text={media.title}
              label="Copy title"
              copiedLabel="Title copied"
              compact
              className="mt-0.5 shrink-0"
            />
          </div>

          <dl className="mt-4 grid gap-2 text-sm">
            {media.uploader && (
              <div className="flex items-center gap-2 text-soft">
                <dt className="sr-only">Uploader</dt>
                <UserRound className="h-3.5 w-3.5 text-muted" aria-hidden="true" />
                <dd className="truncate font-[600]">{media.uploader}</dd>
              </div>
            )}
            <div className="flex items-center gap-2 text-soft">
              <dt className="sr-only">Source link</dt>
              <Link2 className="h-3.5 w-3.5 flex-none text-muted" aria-hidden="true" />
              <dd className="min-w-0 flex-1 truncate font-mono text-[0.72rem] text-muted">
                {media.sourceUrl}
              </dd>
              <CopyButton
                text={media.sourceUrl}
                label="Copy URL"
                copiedLabel="URL copied"
                compact
              />
            </div>
          </dl>

          <div className="mt-4 flex flex-wrap gap-2">
            <span className="tag tag-accent">{media.videoOptions.length} video format{media.videoOptions.length === 1 ? '' : 's'}</span>
            {media.audioOptions.length > 0 && <span className="tag">Audio available</span>}
            {media.captions.length > 0 && <span className="tag">Captions available</span>}
          </div>
        </div>
      </div>

      <div className="mt-5 border-t border-line pt-4">
        <div className="mb-2 flex items-center justify-between gap-3">
          <h3 className="flex items-center gap-2 font-sans text-[0.72rem] font-[750] uppercase tracking-[0.1em] text-muted">
            <FileText className="h-3.5 w-3.5" aria-hidden="true" />
            Post description
          </h3>
          {media.description && (
            <CopyButton
              text={media.description}
              label="Copy description"
              copiedLabel="Description copied"
              compact
            />
          )}
        </div>

        {media.description ? (
          <>
            <p
              className={`whitespace-pre-wrap break-words text-sm leading-relaxed text-soft ${!expanded && longDescription ? 'line-clamp-4' : ''}`}
            >
              {media.description}
            </p>
            {longDescription && (
              <button
                type="button"
                className="btn btn-ghost btn-sm mt-1 !px-0 text-accent-ink"
                onClick={() => setExpanded((value) => !value)}
                aria-expanded={expanded}
              >
                {expanded ? 'Show less' : 'Show full description'}
              </button>
            )}
          </>
        ) : (
          <p className="text-sm text-muted">
            This post did not include a description. The video can still be downloaded if a format is
            listed below.
          </p>
        )}
      </div>
    </section>
  );
}
