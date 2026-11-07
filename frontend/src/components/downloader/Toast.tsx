import { AlertCircle, CheckCircle2, Info, X } from 'lucide-react';

export type ToastTone = 'success' | 'error' | 'info';

interface Props {
  message: string;
  tone?: ToastTone;
  onClose: () => void;
}

export function Toast({ message, tone = 'info', onClose }: Props) {
  const Icon = tone === 'success' ? CheckCircle2 : tone === 'error' ? AlertCircle : Info;

  return (
    <div
      className="fixed bottom-5 left-1/2 z-[80] w-[min(92vw,26rem)] -translate-x-1/2 animate-rise"
      role="status"
      aria-live="polite"
    >
      <div className="flex items-start gap-3 rounded-md border border-line-strong bg-raised px-4 py-3 text-sm text-ink shadow-float">
        <Icon
          className={`mt-0.5 h-4 w-4 flex-none ${tone === 'success' ? 'text-success' : tone === 'error' ? 'text-danger' : 'text-accent'}`}
          aria-hidden="true"
        />
        <p className="flex-1 leading-snug">{message}</p>
        <button
          type="button"
          className="btn btn-ghost !min-h-0 !p-1"
          onClick={onClose}
          aria-label="Dismiss notification"
        >
          <X className="h-3.5 w-3.5" aria-hidden="true" />
        </button>
      </div>
    </div>
  );
}
