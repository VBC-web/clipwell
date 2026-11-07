import { AlertCircle, CheckCircle2, Download, LoaderCircle, RotateCcw } from 'lucide-react';
import type { DownloadJob } from '../../lib/api';
import { apiUrl, formatBytes } from '../../lib/api';

interface Props {
  job: DownloadJob;
  onRetry: () => void;
}

const stageLabels: Record<DownloadJob['status'], string> = {
  queued: 'Waiting for a download slot',
  downloading: 'Downloading from the platform',
  processing: 'Preparing the file',
  ready: 'Your file is ready',
  error: 'The download could not be completed',
  expired: 'This download has expired',
};

export function DownloadProgress({ job, onRetry }: Props) {
  const isTerminal = job.status === 'ready' || job.status === 'error' || job.status === 'expired';
  const displayProgress = job.status === 'processing' ? Math.max(job.progress, 94) : job.progress;

  if (job.status === 'ready' && job.downloadUrl) {
    return (
      <div className="mt-4 rounded-md border border-[color-mix(in_srgb,var(--success)_30%,var(--line))] bg-success-soft p-4 animate-fade" aria-live="polite">
        <div className="flex items-start gap-3">
          <CheckCircle2 className="mt-0.5 h-5 w-5 flex-none text-success" aria-hidden="true" />
          <div className="min-w-0 flex-1">
            <p className="text-sm font-[700] text-success">Download ready</p>
            <p className="mt-0.5 break-all text-xs text-success/90">
              {job.filename}
              {job.sizeBytes ? ` · ${formatBytes(job.sizeBytes)}` : ''}
            </p>
            <div className="mt-3 flex flex-wrap items-center gap-2">
              <a
                href={apiUrl(job.downloadUrl)}
                className="btn btn-primary btn-sm"
                download={job.filename || undefined}
                rel="noopener"
              >
                <Download className="h-3.5 w-3.5" aria-hidden="true" />
                Save file
              </a>
              <span className="text-[0.7rem] text-success/80">
                Temporary storage is cleaned automatically.
              </span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (job.status === 'error' || job.status === 'expired') {
    return (
      <div className="mt-4 rounded-md border border-[color-mix(in_srgb,var(--danger)_28%,var(--line))] bg-danger-soft p-4 animate-fade" role="alert">
        <div className="flex items-start gap-3">
          <AlertCircle className="mt-0.5 h-5 w-5 flex-none text-danger" aria-hidden="true" />
          <div className="min-w-0 flex-1">
            <p className="text-sm font-[700] text-danger">{stageLabels[job.status]}</p>
            <p className="mt-1 text-xs leading-relaxed text-danger/90">
              {job.error || job.message || 'The platform stopped responding. Please try again.'}
            </p>
            <button type="button" className="btn btn-secondary btn-sm mt-3" onClick={onRetry}>
              <RotateCcw className="h-3.5 w-3.5" aria-hidden="true" />
              Try again
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="mt-4 rounded-md border border-line bg-sunken/60 p-4 animate-fade" aria-live="polite">
      <div className="flex items-center justify-between gap-3">
        <div className="flex min-w-0 items-center gap-2">
          <LoaderCircle className="h-4 w-4 flex-none animate-spin text-accent" aria-hidden="true" />
          <p className="truncate text-sm font-[650] text-ink">
            {job.stage || stageLabels[job.status]}
          </p>
        </div>
        <span className="text-xs font-[700] tabular-nums text-muted">{Math.round(displayProgress)}%</span>
      </div>

      <div
        className="mt-3 h-1.5 overflow-hidden rounded-full bg-line"
        role="progressbar"
        aria-label="Download progress"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={Math.round(displayProgress)}
      >
        <div
          className="h-full rounded-full bg-accent transition-[width] duration-500 ease-out"
          style={{ width: `${Math.max(2, displayProgress)}%` }}
        />
      </div>

      <p className="mt-2 text-[0.72rem] text-muted">
        {job.message || 'Keep this tab open. Large videos can take a minute to process.'}
      </p>
      {!isTerminal && (
        <p className="sr-only">
          {stageLabels[job.status]}. {Math.round(displayProgress)} percent complete.
        </p>
      )}
    </div>
  );
}
