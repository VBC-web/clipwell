import { useState } from 'react';
import { AlertCircle, Captions, Download, FileText, LoaderCircle, Music2 } from 'lucide-react';
import { fetchCaptions, type CaptionContent, type MediaInfo } from '../../lib/api';
import { downloadText, safeFilename } from '../../lib/clipboard';
import { CopyButton } from './CopyButton';

interface Props {
  media: MediaInfo;
}

export function CaptionPanel({ media }: Props) {
  const [selectedKey, setSelectedKey] = useState(() => {
    const first = media.captions[0];
    return first ? `${first.lang}:${first.auto}` : '';
  });
  const [content, setContent] = useState<CaptionContent | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const selected = media.captions.find((track) => `${track.lang}:${track.auto}` === selectedKey);

  async function loadCaptions() {
    if (!selected || loading) return;
    setLoading(true);
    setError(null);
    setContent(null);

    try {
      const result = await fetchCaptions(media.mediaId, selected.lang, selected.auto);
      setContent(result);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'That caption track could not be loaded. The platform may no longer provide it.',
      );
    } finally {
      setLoading(false);
    }
  }

  if (media.captions.length === 0) {
    return (
      <div className="rounded-md border border-line bg-sunken/50 p-6 text-center">
        <Captions className="mx-auto h-6 w-6 text-muted" aria-hidden="true" />
        <p className="mt-3 text-sm font-[650] text-ink">No caption tracks were provided</p>
        <p className="mx-auto mt-1 max-w-md text-xs leading-relaxed text-muted">
          This does not affect the video download. Clipwell only offers captions when the public
          source exposes a subtitle or auto-caption track.
        </p>
      </div>
    );
  }

  const filenameBase = safeFilename(media.title, 'clipwell-captions');

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-sm font-[700] text-ink">Caption tracks</p>
          <p className="mt-1 text-xs leading-relaxed text-muted">
            Manual tracks are preferred. Auto-generated captions can contain recognition errors.
          </p>
        </div>
        <span className="tag">{media.captions.length} track{media.captions.length === 1 ? '' : 's'}</span>
      </div>

      <div
        className="scrollbar-thin max-h-56 overflow-y-auto rounded-md border border-line"
        role="radiogroup"
        aria-label="Choose a caption track"
      >
        {media.captions.map((track) => {
          const key = `${track.lang}:${track.auto}`;
          const checked = key === selectedKey;
          return (
            <label
              key={key}
              className={`flex cursor-pointer items-center gap-3 border-b border-line px-3 py-2.5 last:border-b-0 ${
                checked ? 'bg-accent-soft/70' : 'bg-surface hover:bg-sunken/60'
              }`}
            >
              <input
                type="radio"
                name={`caption-track-${media.mediaId}`}
                value={key}
                checked={checked}
                onChange={() => {
                  setSelectedKey(key);
                  setContent(null);
                  setError(null);
                }}
                className="h-3.5 w-3.5 accent-[var(--accent)]"
              />
              <span className="min-w-0 flex-1">
                <span className="block truncate text-sm font-[600] text-ink">{track.label}</span>
                <span className="block text-[0.68rem] uppercase tracking-[0.07em] text-muted">
                  {track.lang}
                  {track.auto ? ' · Auto-generated' : ' · Creator provided'}
                </span>
              </span>
              {track.auto ? (
                <span className="tag">Auto</span>
              ) : (
                <span className="tag tag-success">Manual</span>
              )}
            </label>
          );
        })}
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-2">
        <button
          type="button"
          className="btn btn-secondary btn-sm"
          onClick={loadCaptions}
          disabled={!selected || loading}
        >
          {loading ? (
            <LoaderCircle className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />
          ) : (
            <Captions className="h-3.5 w-3.5" aria-hidden="true" />
          )}
          {loading ? 'Loading captions…' : 'Load selected captions'}
        </button>
        <span className="text-[0.7rem] text-muted">Plain text, SRT or copy to clipboard</span>
      </div>

      {error && (
        <div className="mt-3 flex items-start gap-2 rounded-sm bg-danger-soft p-3 text-xs leading-relaxed text-danger" role="alert">
          <AlertCircle className="mt-0.5 h-4 w-4 flex-none" aria-hidden="true" />
          <span>{error}</span>
        </div>
      )}

      {loading && (
        <div className="mt-4 space-y-2" aria-hidden="true">
          <div className="skeleton h-3 w-4/5 rounded-sm" />
          <div className="skeleton h-3 w-full rounded-sm" />
          <div className="skeleton h-3 w-3/5 rounded-sm" />
        </div>
      )}

      {content && (
        <div className="mt-4 animate-fade">
          <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center gap-2 text-[0.72rem] font-[700] uppercase tracking-[0.08em] text-muted">
              <FileText className="h-3.5 w-3.5" aria-hidden="true" />
              {content.label}
              {content.auto && <span className="tag">Auto-generated</span>}
            </div>
            <div className="flex flex-wrap items-center gap-1">
              <CopyButton
                text={content.text}
                label="Copy text"
                copiedLabel="Captions copied"
                compact
              />
              <button
                type="button"
                className="btn btn-ghost btn-sm !min-h-8 !gap-1.5 !px-2 !py-1 text-[0.72rem]"
                onClick={() => downloadText(`${filenameBase}.${content.lang}.srt`, content.srt, 'application/x-subrip')}
              >
                <Download className="h-3.5 w-3.5" aria-hidden="true" />
                SRT
              </button>
              <button
                type="button"
                className="btn btn-ghost btn-sm !min-h-8 !gap-1.5 !px-2 !py-1 text-[0.72rem]"
                onClick={() => downloadText(`${filenameBase}.${content.lang}.txt`, content.text, 'text/plain')}
              >
                <Download className="h-3.5 w-3.5" aria-hidden="true" />
                TXT
              </button>
            </div>
          </div>
          <pre className="scrollbar-thin max-h-72 overflow-auto whitespace-pre-wrap break-words rounded-md border border-line bg-sunken/45 p-3 font-sans text-xs leading-relaxed text-soft">
            {content.text}
          </pre>
          <p className="mt-2 flex items-center gap-1.5 text-[0.68rem] text-muted">
            <Music2 className="h-3 w-3" aria-hidden="true" />
            Captions are returned as the platform exposes them. Review auto-generated text before
            quoting it.
          </p>
        </div>
      )}
    </div>
  );
}
