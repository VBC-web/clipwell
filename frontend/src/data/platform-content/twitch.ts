import type { PlatformContent } from './types';

export const twitch: PlatformContent = {
  key: 'twitch',
  metaTitle: 'Twitch Video Downloader — Save VODs & Clips | Clipwell',
  metaDescription:
    'Download public Twitch VODs, highlights and clips in the qualities Twitch exposes. No live capture, no chat, no account login. See available formats before saving.',
  eyebrow: 'Twitch downloader',
  headline: 'Twitch VODs and clips,',
  headlineAccent: 'without screen recording.',
  intro: [
    'Saving a Twitch VOD with a screen recorder is slow, lossy and dependent on how long you leave a browser open. Clipwell works from the public VOD or clip link instead, reads the available renditions and downloads the file the platform is already serving.',
    'This is not a live-stream recorder. A channel page, an active broadcast and a chat archive are all out of scope. For finished VODs, highlights and clips, the tool keeps the stream title, channel name, duration and real quality options together, including muted audio segments if the source contains them.',
  ],
  glance: [
    'Public Twitch VODs, highlights and clips',
    'Source renditions from the platform, not upscaled copies',
    'No live recording, chat capture or login bypass',
  ],
  steps: [
    {
      title: 'Copy the VOD or clip URL',
      body: 'VODs usually use twitch.tv/videos/ followed by a number. Clips can live on clips.twitch.tv or under a channel’s /clip/ path. A bare channel URL is a live page and is not accepted.',
    },
    {
      title: 'Check the detected platform',
      body: 'Clipwell validates Twitch hosts and the video path before extraction. If you paste a Kick or YouTube link by mistake, the page offers the matching downloader with the URL preserved.',
    },
    {
      title: 'Pick a rendition and download',
      body: 'Twitch VODs can expose several quality levels; clips often expose fewer. Review the real list, start the job and follow the progress. Temporary storage is cleaned up automatically.',
    },
  ],
  features: [
    {
      title: 'VOD and clip support',
      body: 'The URL policy understands standard VOD paths and clip domains, so you can use the link you already have instead of converting it first.',
    },
    {
      title: 'What you see is what is served',
      body: 'Quality options come from Twitch’s public playback data. If a VOD only offers 720p to anonymous viewers, the menu shows 720p. No label promises a rendition the platform did not return.',
    },
    {
      title: 'Muted segments stay honest',
      body: 'Twitch sometimes mutes VOD audio for rights reasons. Clipwell does not unmute, replace or synthesize that audio. The download reflects the public VOD, including any silent sections.',
    },
    {
      title: 'Text tools without invented data',
      body: 'Copy the title and description, and use caption tracks only if Twitch exposes them. The interface clearly distinguishes “not available” from “still loading.”',
    },
  ],
  problems: [
    {
      problem: 'The VOD audio is silent in places',
      solution:
        'Twitch mutes some VOD audio to comply with music rights. Clipwell cannot and does not reverse that. The muted sections are part of the public source; use a different VOD or the broadcaster’s own archive if you need complete audio.',
    },
    {
      problem: 'The channel URL is rejected',
      solution:
        'A channel page is a live destination, not a VOD. Open Past Broadcasts or the specific clip and copy that URL. The address should include /videos/ or /clip/ or use the clips.twitch.tv domain.',
    },
    {
      problem: 'The clip has disappeared',
      solution:
        'Clips can be deleted by the creator, expire under channel settings, or be region-restricted. If it no longer opens publicly, Clipwell cannot recover it. Retry only after confirming the clip still plays in a private window.',
    },
  ],
  faqs: [
    {
      question: 'Can Clipwell record a live Twitch stream?',
      answer:
        'No. Live recording is explicitly unsupported. Clipwell downloads finished public VODs, highlights and clips. If the broadcast is still live, wait for the VOD or use the broadcaster’s own export tools if available.',
    },
    {
      question: 'Why are some parts of a Twitch VOD muted?',
      answer:
        'Twitch applies audio muting to certain VODs for music licensing reasons. The mute is embedded in the public playback experience. Clipwell does not bypass it or replace the audio with a different track.',
    },
    {
      question: 'Does it download Twitch chat?',
      answer:
        'No. Chat is separate from the video and is not captured. The result is a media file, not a page archive. If you need chat for research or moderation, use a dedicated chat-logging tool that respects the channel and platform rules.',
    },
    {
      question: 'Are Twitch clips available in 1080p?',
      answer:
        'Only if Twitch exposes a 1080p rendition for that clip. Clips are often lower resolution than the source broadcast because they are short, separate transcodes. Clipwell reports the actual options rather than offering a 1080p label by default.',
    },
    {
      question: 'Can I download subscriber-only VODs?',
      answer:
        'No. Subscriber-only, private or deleted VODs are outside the public scope of the service. Clipwell does not accept Twitch credentials or session cookies. Use the platform’s own access controls for content you are entitled to view.',
    },
  ],
  article: {
    title: 'What you can and cannot save from Twitch',
    intro:
      'Twitch is built for live moments, but most of what people want to keep is already archived: a VOD, a highlight or a clip. Understanding which of those you have and what the platform exposes will save you from failed downloads and unrealistic quality expectations.',
    sections: [
      {
        heading: 'VODs, highlights and clips are different assets',
        body: [
          'A VOD is the full replay of a broadcast, usually addressed with /videos/ and a numeric ID. A highlight is an edited excerpt the creator published. A clip is a short, separate transcode created by a viewer or the channel. Each can expose a different set of qualities and caption availability.',
          'Clipwell accepts the public URL for each. It does not convert a live channel into a VOD, and it does not discover a hidden highlight behind a channel page. The link needs to point at the asset you actually want.',
        ],
      },
      {
        heading: 'Why Twitch VOD audio can go silent',
        body: [
          'Music rights are the usual reason. Twitch may mute portions of a VOD where it detects copyrighted audio, while leaving the live broadcast unchanged. The mute is part of the archived file, not a bug in the downloader. Clipwell returns the public archive as it is.',
          'If complete audio matters, check the VOD before downloading. The mute pattern is visible during playback. A third-party downloader cannot restore audio that the platform removed from the public asset.',
        ],
      },
      {
        heading: 'Archiving your own channel responsibly',
        body: [
          'Creators often want their own broadcasts for editing or backup. Clipwell can download a public VOD you own, but it is not a retention guarantee. Twitch may expire VODs based on channel settings and time. A local archive is useful only if you download before the expiry date.',
          'If other people appear in the stream, treat the archive with the same care you would the live broadcast. Do not republish private conversations or third-party music simply because you can save the file. Copyright and consent travel with the recording.',
        ],
      },
    ],
  },
  sourceNotes: [
    'Live streams are not recorded.',
    'Chat is not included in any download.',
    'Rights-related audio mutes in VODs are preserved.',
  ],
};
