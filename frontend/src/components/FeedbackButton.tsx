import { useEffect, useState } from 'react';
import { Flag, MessageSquare, X } from 'lucide-react';
import { apiUrl } from '../lib/api';

const CATEGORIES = ['Bug / Broken Link', 'Feature Request', 'General Experience'] as const;

export default function FeedbackButton() {
  const [open, setOpen] = useState(false);
  const [category, setCategory] = useState<(typeof CATEGORIES)[number]>('Bug / Broken Link');
  const [url, setUrl] = useState('');
  const [message, setMessage] = useState('');
  const [email, setEmail] = useState('');
  const [prefillError, setPrefillError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [done, setDone] = useState(false);

  useEffect(() => {
    function handler(event: Event) {
      const detail = (event as CustomEvent<{ url?: string; error?: string }>).detail || {};
      if (detail.url) setUrl(detail.url);
      if (detail.error) setPrefillError(detail.error);
      setOpen(true);
    }
    window.addEventListener('clipwell:open-feedback', handler);
    return () => window.removeEventListener('clipwell:open-feedback', handler);
  }, []);

  function reset() {
    setDone(false);
    setSubmitting(false);
    setPrefillError(null);
  }

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (!message.trim()) return;
    setSubmitting(true);
    try {
      await fetch(apiUrl('/api/feedback'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ category, message, url: url || null, email: email || null }),
      });
      setDone(true);
      window.setTimeout(() => {
        setOpen(false);
        reset();
        setUrl('');
        setMessage('');
        setEmail('');
        setCategory('Bug / Broken Link');
      }, 1500);
    } catch {
      setDone(false);
      setSubmitting(false);
    }
  }

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="btn btn-secondary btn-sm !min-h-9 gap-1.5"
        aria-label="Send feedback"
      >
        <MessageSquare className="h-3.5 w-3.5" aria-hidden="true" />
        Feedback
      </button>

      {open && (
        <div
          className="fixed inset-0 z-50 grid place-items-center bg-black/60 p-4"
          role="dialog"
          aria-modal="true"
          aria-labelledby="feedback-title"
        >
          <div className="w-full max-w-lg rounded-md border border-line bg-[#141414] p-5 text-ink shadow-2xl">
            <div className="mb-4 flex items-center justify-between gap-3">
              <h2 id="feedback-title" className="font-sans text-base font-[750] text-ink">
                Send feedback
              </h2>
              <button
                type="button"
                onClick={() => {
                  setOpen(false);
                  reset();
                }}
                className="btn btn-ghost btn-sm !min-h-8 !px-2"
                aria-label="Close feedback"
              >
                <X className="h-4 w-4" aria-hidden="true" />
              </button>
            </div>

            {done ? (
              <p className="rounded-md border border-line bg-surface p-4 text-sm text-soft">
                Thanks! Your report has been logged.
              </p>
            ) : (
              <form onSubmit={submit} className="space-y-4">
                <div>
                  <p className="mb-2 text-xs font-[700] uppercase tracking-[0.1em] text-muted">
                    Category
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {CATEGORIES.map((item) => (
                      <button
                        key={item}
                        type="button"
                        onClick={() => setCategory(item)}
                        className={`rounded-full border px-3 py-1.5 text-xs font-[650] transition-colors ${
                          category === item
                            ? 'border-accent bg-accent text-white'
                            : 'border-line bg-surface text-soft hover:border-line-strong'
                        }`}
                      >
                        {item}
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="field-label" htmlFor="feedback-url">
                    Link URL (optional)
                  </label>
                  <input
                    id="feedback-url"
                    type="url"
                    className="text-input"
                    value={url}
                    onChange={(event) => setUrl(event.target.value)}
                    placeholder="https://..."
                  />
                </div>

                {prefillError && (
                  <p className="rounded-md border border-danger/30 bg-danger-soft px-3 py-2 text-xs text-danger">
                    {prefillError}
                  </p>
                )}

                <div>
                  <label className="field-label" htmlFor="feedback-message">
                    Message / details
                  </label>
                  <textarea
                    id="feedback-message"
                    className="text-input min-h-[7rem]"
                    value={message}
                    onChange={(event) => setMessage(event.target.value)}
                    placeholder="Tell us what happened, which platform failed, or what we should improve..."
                    required
                  />
                </div>

                <div>
                  <label className="field-label" htmlFor="feedback-email">
                    Contact email (optional)
                  </label>
                  <input
                    id="feedback-email"
                    type="email"
                    className="text-input"
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                    placeholder="Email (optional, if you'd like an update)"
                    required
                  />
                </div>

                <div className="flex justify-end gap-2 pt-1">
                  <button
                    type="button"
                    onClick={() => {
                      setOpen(false);
                      reset();
                    }}
                    className="btn btn-ghost btn-sm"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled
                    className="btn btn-primary btn-sm opacity-60"
                    title="Feedback submission is temporarily disabled"
                  >
                    <Flag className="h-4 w-4" aria-hidden="true" />
                    Temporarily unavailable
                  </button>
                </div>
                <p className="text-xs text-muted">
                  Feedback submission is temporarily disabled. Please check back later.
                </p>
              </form>
            )}
          </div>
        </div>
      )}
    </>
  );
}