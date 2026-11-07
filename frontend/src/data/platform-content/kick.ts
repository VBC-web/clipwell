import type { PlatformContent } from './types';

export const kick: PlatformContent = {
  key: 'kick',
  metaTitle: 'Kick Video Downloader — Save Public VODs & Clips | Clipwell',
  metaDescription:
    'Download public Kick VODs and clips with the formats Kick exposes. View stream details and save the available file. Live channels are not recorded. Public links only.',
  eyebrow: 'Kick downloader',
  headline: 'Kick VODs and clips,',
  headlineAccent: 'ready when you are.',
  intro: [
    'Kick stores past broadcasts and clips differently, and the links can look almost identical to a live channel page. Clipwell checks for a VOD or clip identifier before extraction, then presents the source’s real formats rather than a generic download menu.',
    'Live channels are not recorded. A stream that is still running does not have the finished file this tool is designed to save. If a replay or clip is public, paste its direct link and Clipwell will report what the platform exposes, including a clear message when no captions or separate audio track exist.',
  ],
  glance: [
    'Public Kick VODs and clip pages',
    'Source quality and estimated size where reported',
    'No live recording and no chat capture',
  ],
  steps: [
    {
      title: 'Open the VOD or clip, not the live channel',
      body: 'A Kick clip URL usually carries a clip parameter, while a VOD link points at a past broadcast. Copy the address from the individual video view. A bare kick.com/channel URL is a live channel page and is rejected.',
    },
    {
      title: 'Paste the direct link',
      body: 'Clipwell confirms the host and media shape before contacting the API. Links from other platforms are caught by the detector and offered a route to the correct downloader.',
    },
    {
      title: 'Download the available file',
      body: 'Choose from the returned quality options. Kick may only expose one rendition for a clip, especially a short one. The job streams progress and the temporary file is removed after expiry.',
    },
  ],
  features: [
    {
      title: 'VODs and clips are distinct',
      body: 'The page understands both URL families and does not treat a live channel page as a downloadable VOD. That avoids the most common Kick link error.',
    },
    {
      title: 'Stream details first',
      body: 'See the channel, title, duration and thumbnail before downloading. For clips, the limited runtime and available format set are visible up front.',
    },
    {
      title: 'No chat or live capture',
      body: 'Clipwell saves the public video file only. It does not record a running stream, capture chat, or archive a channel. Those are different operations with different privacy and consent implications.',
    },
    {
      title: 'Clear missing-caption state',
      body: 'Kick does not expose subtitle tracks for every VOD or clip. When no captions are available, the panel says so. No blank SRT is generated.',
    },
  ],
  problems: [
    {
      problem: 'The link is rejected as a channel page',
      solution:
        'Copy the URL while watching the VOD or clip itself. A bare kick.com/username address points at the live channel and does not identify a finished video. Look for a video or clip query parameter in the URL.',
    },
    {
      problem: 'A VOD that worked before is now gone',
      solution:
        'Kick and broadcasters can remove VODs or change their availability. Clipwell cannot retrieve a file the platform no longer serves. Check that the VOD still opens publicly before retrying.',
    },
    {
      problem: 'No captions are listed',
      solution:
        'Most Kick clips do not include subtitle tracks. Clipwell only shows captions when the public source exposes them. You can still copy the description or title, but the tool will not invent a transcript.',
    },
  ],
  faqs: [
    {
      question: 'Can Clipwell record a live Kick stream?',
      answer:
        'No. Live recording is not part of this downloader. Clipwell handles public VODs and clips that already exist as finished media. Recording a live stream would require a different tool and raises separate consent and terms considerations.',
    },
    {
      question: 'Which Kick link formats are supported?',
      answer:
        'Direct links containing a video or clip identifier are supported, including the common ?video= and ?clip= query forms and paths that include /video, /videos, /clip or /clips. A bare channel URL is not a media URL and will be rejected.',
    },
    {
      question: 'Why is the clip quality lower than the stream?',
      answer:
        'Kick creates clip renditions that may be smaller than the original broadcast. Clipwell can only download the clip file the platform exposes. It does not reconstruct the full-resolution source from a lower-quality clip.',
    },
    {
      question: 'Are Kick chat messages saved?',
      answer:
        'No. Chat is not part of the video stream and is not captured or included in the download. Clipwell returns a media file, not an archive of the channel page or its community activity.',
    },
    {
      question: 'Can I download a Kick VOD from a private channel?',
      answer:
        'No. The service accepts public media only. Deleted, subscriber-only or login-gated content is not accessible. Clipwell does not accept account cookies or bypass channel restrictions.',
    },
  ],
  article: {
    title: 'Kick VOD links vs. clip links: a short field guide',
    intro:
      'Kick’s viewing experience is simple, but its URLs are not always obvious. A page that looks like a video can be a live channel, and a clip can share the same path as the channel with only a query parameter to distinguish it. Getting the right URL is most of the battle.',
    sections: [
      {
        heading: 'How to tell you have a VOD or clip',
        body: [
          'A VOD address identifies a past broadcast and usually includes a video parameter or a /video path. A clip link includes a clip identifier, commonly in a clip query parameter or a /clip path. If the address is simply the channel name, you are on the live page, even if a video is playing in a pinned player.',
          'Clipwell validates the shape of the link before extraction. That is deliberate: sending a channel URL to a media extractor can produce confusing errors or, worse, an unexpected long-running job. A direct rejection with an explanation is more useful.',
        ],
      },
      {
        heading: 'Why clips have fewer formats',
        body: [
          'A short clip may be transcoded once for quick playback. Unlike a full VOD, there is often no ladder of 144p through 4K renditions. Clipwell lists the actual file or files and reports the resolution, format and estimated size where Kick supplies them.',
          'This is also why you should not expect captions on every clip. Caption tracks are a separate asset, not a property of the video container. If the source does not provide one, there is nothing to download.',
        ],
      },
      {
        heading: 'What this tool deliberately leaves out',
        body: [
          'Clipwell does not record live streams, save chat, or archive channels. It does not require a Kick login and will not accept cookies to reach subscriber-only content. That keeps the service focused and makes its privacy story easier to understand.',
          'If you are saving your own broadcast for an archive, check the platform’s retention controls and download the VOD while it is still available. Platforms expire old broadcasts, and a downloader cannot restore one that has already been removed.',
        ],
      },
    ],
  },
  sourceNotes: [
    'Live streams are not recorded; only finished public VODs and clips work.',
    'Chat and channel pages are not captured.',
    'Caption tracks are rarely present and are never invented.',
  ],
};
