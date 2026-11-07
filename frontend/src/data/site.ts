export const SITE = {
  name: 'Clipwell',
  legalName: 'Clipwell',
  tagline: 'Public media, saved cleanly.',
  description:
    'Download public videos, audio and captions from seven major platforms with a clean, privacy-minded downloader.',
  email: 'hello@clipwell.app',
  supportEmail: 'support@clipwell.app',
  privacyEmail: 'privacy@clipwell.app',
  legalEmail: 'legal@clipwell.app',
  dmcaEmail: 'dmca@clipwell.app',
  lastUpdated: 'November 7, 2026',
  defaultTitle:
    'Clipwell — Download Public Videos from YouTube, TikTok, Instagram & More',
  defaultDescription:
    'Paste a public video link from YouTube, Instagram, TikTok, Twitch, X, Facebook or Kick. Choose only the formats available, with captions and audio when the source provides them.',
} as const;

export const NAV_LINKS = [
  { label: 'Platforms', href: '/#platforms' },
  { label: 'How it works', href: '/#how-it-works' },
  { label: 'About', href: '/about/' },
] as const;

export const LEGAL_LINKS = [
  { label: 'Privacy Policy', href: '/privacy-policy/' },
  { label: 'Terms of Service', href: '/terms-of-service/' },
  { label: 'Copyright Policy', href: '/copyright-policy/' },
  { label: 'DMCA Policy', href: '/dmca-policy/' },
  { label: 'Disclaimer', href: '/disclaimer/' },
  { label: 'Contact', href: '/contact/' },
] as const;

export const HOME_FAQS = [
  {
    question: 'Is Clipwell free to use?',
    answer:
      'Yes. Clipwell does not require an account or payment. The public deployment enforces request and file-size limits to keep the service available, so unusually large or frequent downloads may be refused.',
  },
  {
    question: 'Can I download private videos or content that requires a login?',
    answer:
      'No. Clipwell only handles public links. It does not accept cookies, passwords, private posts, age-restricted content or anything behind a platform login. It also does not bypass DRM or other access controls.',
  },
  {
    question: 'Does Clipwell store the videos I download?',
    answer:
      'Downloads are written to temporary storage and removed automatically, normally within 15 minutes. Clipwell does not build a media library or keep a copy after the job expires. See the Privacy Policy for details.',
  },
  {
    question: 'Why are only some video qualities shown?',
    answer:
      'The list is generated from the formats the platform actually exposes for that specific post. If a video only has a 720p stream, you will see 720p rather than a menu of invented resolutions.',
  },
  {
    question: 'What happens when a link is from the wrong platform?',
    answer:
      'Clipwell detects the platform before sending anything to the backend. If you paste an Instagram link into the TikTok downloader, it tells you which downloader to use and gives you a button to open it with the link already filled in.',
  },
  {
    question: 'Can I download captions and audio separately?',
    answer:
      'When the public source provides subtitle tracks, Clipwell can return them as SRT or plain text. Audio-only MP3 or M4A options appear when a usable audio stream is available. Captions are not invented when none exist.',
  },
  {
    question: 'Why does a download sometimes fail?',
    answer:
      'Platforms regularly change their pages, add login walls, restrict content by region or challenge automated requests. Clipwell reports the reason instead of pretending the download worked. Retrying later or choosing a different public post often resolves temporary failures.',
  },
  {
    question: 'Am I allowed to download and reuse a video?',
    answer:
      'Only if you have the right to do so. Public visibility does not transfer copyright. Download your own content, content licensed for reuse, or content covered by a valid exception in your jurisdiction. Clipwell is a utility, not a licence to republish someone else’s work.',
  },
] as const;
