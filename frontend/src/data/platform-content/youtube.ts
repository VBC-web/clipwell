import type { PlatformContent } from './types';

export const youtube: PlatformContent = {
  key: 'youtube',
  metaTitle: 'YouTube Video Downloader — MP4, Audio & Captions | Clipwell',
  metaDescription:
    'Download public YouTube videos and Shorts in available resolutions, or save audio and captions. Clipwell shows only real formats and explains platform restrictions.',
  eyebrow: 'YouTube downloader',
  headline: 'See the formats.',
  headlineAccent: 'Keep the video.',
  intro: [
    'YouTube is unusually generous with resolution options and unusually strict about how those streams are served. Clipwell reads the public manifest for one video and turns it into a clear list: 360p, 720p, 1080p, 1440p, 4K or whatever else is genuinely present, plus audio-only and caption options when they exist.',
    'It does not use cookies, browser sessions or private APIs. That keeps the tool on the right side of access controls, but it also means a video that triggers YouTube’s bot verification may be unavailable for a while. When that happens, you will see a direct explanation instead of a broken download.',
  ],
  glance: [
    'Public videos, Shorts and ended live replays',
    'Resolution tiers from 144p through 2160p when offered',
    'Manual and auto-generated captions when exposed',
  ],
  steps: [
    {
      title: 'Copy a single-video URL',
      body: 'Use the share action on the video or Short. Standard watch URLs, youtu.be links, Shorts links, live replay links and embed links are accepted. A channel page or a pure playlist does not identify one video and will be rejected.',
    },
    {
      title: 'Paste and extract',
      body: 'Clipwell checks the YouTube host and video identifier before sending the request. The backend fetches public metadata only; it does not sign in or download the whole file just to show the details.',
    },
    {
      title: 'Choose a resolution or audio track',
      body: 'Video options are merged to MP4 where the streams allow it. Pick a caption track separately if you want subtitles. Progress is reported through the job, and the temporary file is removed after expiry.',
    },
  ],
  features: [
    {
      title: 'Honest resolution tiers',
      body: 'The quality menu is built from the source’s video streams. A 4K label appears only if a 2160p stream exists. Lower tiers are offered from actual streams rather than upscaled copies.',
    },
    {
      title: 'Video, audio or captions',
      body: 'Download a merged MP4, an audio-only file, or a subtitle track in a separate step. Keeping these separate avoids pretending that every video has a clean audio-only master or human-written captions.',
    },
    {
      title: 'Auto-caption awareness',
      body: 'Manual and auto-generated tracks are labelled separately. Auto captions can contain recognition errors, so they are useful for searching or accessibility notes but should not be treated as an authoritative transcript.',
    },
    {
      title: 'No hidden playlist expansion',
      body: 'Clipwell processes one public video at a time. It does not quietly queue an entire playlist or download a channel in the background.',
    },
  ],
  problems: [
    {
      problem: 'YouTube asks the server to confirm it is not a bot',
      solution:
        'This is a YouTube-side challenge, usually temporary and more common from data-centre IP addresses. Clipwell does not use cookies to get around it. Wait and retry, try another public video, or use a deployment with a different egress network.',
    },
    {
      problem: 'A high resolution is missing from the list',
      solution:
        'The source may not offer it, it may require a signed-in account, or YouTube may be serving a reduced format set. Clipwell only displays what an anonymous extraction returns. A 1080p upload does not guarantee that every tier is available to every client.',
    },
    {
      problem: 'The video is age-restricted or members-only',
      solution:
        'Those videos require an authenticated account and are deliberately unsupported. Clipwell does not accept cookies or bypass access restrictions. Choose a public alternative or use YouTube’s own account features for personal access.',
    },
  ],
  faqs: [
    {
      question: 'Can I download a YouTube video in 4K?',
      answer:
        'If the public video exposes a 2160p stream, 4K will appear in the list and can be merged to MP4. Availability depends on the upload and YouTube’s current formats. Clipwell does not upscale lower-resolution streams to create a 4K file.',
    },
    {
      question: 'Why do some YouTube downloads have no audio option?',
      answer:
        'Audio-only choices are built from separate audio streams exposed by YouTube. If none can be used, the video download may still include audio, but a standalone audio file is not offered. The interface never generates a silent audio file and calls it complete.',
    },
    {
      question: 'Are auto-generated captions available?',
      answer:
        'When YouTube exposes automatic captions for the language, Clipwell lists them separately from creator-provided tracks. They can contain transcription errors and timing quirks. You can download them as SRT or copy the plain text.',
    },
    {
      question: 'Do you support playlists or entire channels?',
      answer:
        'No. Clipwell is intentionally a single-video tool. Paste the URL of the video you want. Bulk downloading would create different load, rights and rate-limit problems, and it is not the product this service offers.',
    },
    {
      question: 'Is downloading YouTube videos permitted?',
      answer:
        'YouTube’s terms and copyright law still apply. Use downloads for content you own, content licensed for reuse, or cases covered by a valid exception such as fair use. Clipwell does not grant permission to copy or redistribute a video.',
    },
  ],
  article: {
    title: 'How to choose the right YouTube download format',
    intro:
      'A YouTube video is not a single file. It is a collection of video and audio streams at different resolutions and codecs. Clipwell’s job is to make that collection legible without exposing raw stream identifiers or pretending every option is equally useful.',
    sections: [
      {
        heading: 'Resolution is not the same as quality',
        body: [
          'A 1080p label tells you the frame height, not whether the source was sharp, whether the codec is efficient, or how much detail survived the upload. YouTube often serves higher resolutions in VP9 or AV1, while lower resolutions may use H.264. Clipwell merges the selected video stream with the best available audio and asks FFmpeg to produce an MP4 where possible.',
          'That process does not improve the original image. It simply packages the chosen streams into a file your device can play. If the highest source is 1080p, choosing 1080p is the original-quality choice; there is no hidden 4K master waiting behind an upgrade button.',
        ],
      },
      {
        heading: 'When 60 fps matters',
        body: [
          'Some videos are published at 60 frames per second, which matters for games, sport and motion-heavy footage. The quality list prioritises a clean, playable result, while the format note tells you the frame rate when the source reports it. A 1080p60 stream is different from a 1080p30 stream even though both carry the same height label.',
          'If the source has both, the extractor chooses a valid high-quality stream for the selected tier. The exact codec depends on what YouTube exposes at that moment; the result is remuxed or transcoded to MP4 only when the streams require it.',
        ],
      },
      {
        heading: 'The bot check is an access control, not a bug to evade',
        body: [
          'YouTube sometimes presents a “confirm you’re not a bot” challenge to anonymous requests from cloud networks. The correct response is to report the condition, not to attach a user’s cookies or rotate through credentials. Clipwell does neither. If you see this message, the video may work later or from a different network.',
          'The same principle applies to private, age-restricted and members-only videos. Clipwell supports public media. It is not a login proxy, a DRM tool or a way to recover content you cannot otherwise access.',
        ],
      },
    ],
  },
  sourceNotes: [
    'Bot verification and region locks can make a public video temporarily unavailable.',
    'Active live streams are not recorded; finished replays may work.',
    'Playlists and channels are intentionally processed one video at a time.',
  ],
};
