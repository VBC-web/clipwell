import { useEffect, useState } from 'react';
import { Check, Copy } from 'lucide-react';
import { copyText } from '../../lib/clipboard';

interface Props {
  text: string;
  label?: string;
  copiedLabel?: string;
  compact?: boolean;
  className?: string;
  onResult?: (ok: boolean) => void;
}

export function CopyButton({
  text,
  label = 'Copy',
  copiedLabel = 'Copied',
  compact = false,
  className = '',
  onResult,
}: Props) {
  const [copied, setCopied] = useState(false);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    if (!copied && !failed) return;
    const timer = window.setTimeout(() => {
      setCopied(false);
      setFailed(false);
    }, 2200);
    return () => window.clearTimeout(timer);
  }, [copied, failed]);

  async function handleCopy() {
    const ok = await copyText(text);
    setCopied(ok);
    setFailed(!ok);
    onResult?.(ok);
  }

  const Icon = copied ? Check : Copy;
  const stateLabel = copied ? copiedLabel : failed ? 'Copy failed' : label;

  return (
    <button
      type="button"
      className={`btn btn-ghost btn-sm ${compact ? '!min-h-8 !gap-1.5 !px-2 !py-1 text-[0.72rem]' : ''} ${copied ? '!text-success' : ''} ${failed ? '!text-danger' : ''} ${className}`}
      onClick={handleCopy}
      aria-live="polite"
      title={failed ? 'Clipboard access was blocked. Select the text and copy it manually.' : stateLabel}
    >
      <Icon className="h-3.5 w-3.5" aria-hidden="true" />
      <span>{stateLabel}</span>
    </button>
  );
}
