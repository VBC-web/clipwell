import type { PlatformContent } from './types';

export const tiktok: PlatformContent = {
  key: 'tiktok',
  metaTitle: 'TikTok Video Downloader — Save Public Videos | Clipwell',
  metaDescription:
    'Save public TikTok videos in the formats TikTok exposes. View creator details, copy descriptions and download captions when available. Photo posts and private videos are unsupported.',
  eyebrow: 'TikTok downloader',
  headline: 'Save the clip.',
  headlineAccent: 'Keep the context.',
  intro: [
    'TikTok links are usually short, often shared through the app, and sometimes stripped of the information a downloader needs. Clipwell accepts standard video URLs and the common short share forms, then verifies that the result is a public video before asking for formats.',
    'The download itself is only part of the job. The creator name, post description, duration, thumbnail and any caption tracks are shown alongside the file options so you can tell one clip from another. Photo posts, private videos and slideshows are not treated as videos.',
  ],
  glance: [
    'Public TikTok videos and short share links',
    'Available MP4 qualities and audio options',
    'Description and caption access where exposed',
  ],
  steps: [
    {
      title: 'Share or copy the public video link',
      body: 'Use TikTok’s Share → Copy link action. Standard /@creator/video/ URLs and the short /t/ share URLs are accepted. If the post opens only inside the app and has no public web view, an anonymous downloader may not be able to read it.',
    },
    {
      title: 'Paste the link above',
      body: 'The detector identifies TikTok before anything is sent to the backend. A link from another platform will produce a clear suggestion rather than a generic extraction error.',
    },
    {
      title: 'Choose from the real format list',
      body: 'TikTok often exposes a small number of renditions. Pick the video quality or audio-only option that appears. The post description and captions can be copied separately from the download panel.',
    },
  ],
  features: [
    {
      title: 'Short links are welcome',
      body: 'You do not have to expand a vm.tiktok.com or /t/ share URL manually. Clipwell validates the host and lets the extractor resolve the destination.',
    },
    {
      title: 'One video at a time',
      body: 'The result is tied to the specific public post. Profile links and search pages are rejected because they do not identify which video should be downloaded.',
    },
    {
      title: 'No invented watermark claims',
      body: 'Clipwell saves the public video as TikTok serves it. It does not advertise watermark removal or alter creator attribution. If the source file includes a watermark, that is the file the platform exposed.',
    },
    {
      title: 'Caption and description tools',
      body: 'Copy the post caption for context, or load an available subtitle track and save it as SRT or TXT. When TikTok exposes neither, the interface tells you instead of producing an empty file.',
    },
  ],
  problems: [
    {
      problem: 'The short link will not resolve',
      solution:
        'Some region-specific short domains and expired share links cannot be reached from the backend’s network. Open the video in TikTok, use Copy link again, and check that it opens in a browser without signing in. If the link is app-only, try the full /@creator/video/ URL.',
    },
    {
      problem: 'A photo post is rejected',
      solution:
        'TikTok photo carousels are not videos, even when they include music. Clipwell is a video downloader, so it requires an actual video stream. Use a different post or save your own photo set through TikTok’s account tools.',
    },
    {
      problem: 'The download has a watermark',
      solution:
        'Clipwell does not remove platform or creator watermarks. The available file comes from the public source. The honest result is the source file, not a modified copy that might strip attribution or violate platform terms.',
    },
  ],
  faqs: [
    {
      question: 'Can I remove the TikTok watermark with Clipwell?',
      answer:
        'No. Clipwell does not offer watermark removal or promise an unwatermarked file. It downloads the public video as TikTok exposes it. Stripping attribution can also raise copyright and platform-terms issues.',
    },
    {
      question: 'Do photo slideshows work?',
      answer:
        'No. TikTok photo posts do not contain a single downloadable video stream. The URL validator rejects them as non-video content. Standard videos and some animated posts with video streams are handled normally.',
    },
    {
      question: 'Why is only one video quality available?',
      answer:
        'TikTok frequently exposes a single mobile-optimised rendition for a post. Clipwell lists what it finds, including file size and format notes when available. It will not create fake 1080p or 4K options from a smaller source.',
    },
    {
      question: 'Can I download the sound from a TikTok?',
      answer:
        'An audio-only option appears only when a separate usable audio stream is exposed or can be extracted cleanly from the video. Music licensing still applies. Downloading a sound does not give you permission to reuse the track in another video.',
    },
    {
      question: 'Does Clipwell support private TikTok accounts?',
      answer:
        'No. Private videos, friends-only posts and login-gated content are not supported. Clipwell does not accept TikTok cookies or credentials and does not attempt to bypass access controls.',
    },
  ],
  article: {
    title: 'TikTok download links: short shares, full URLs and what actually works',
    intro:
      'TikTok is built around app sharing, and its links show it. A copied link may be a compact /t/ URL, a full creator/video address, or something generated by a regional app version. The public destination is what matters, and it still has to be a video.',
    sections: [
      {
        heading: 'Short link, full link, or neither',
        body: [
          'Short share URLs are convenient because they hide the creator handle and video ID. Clipwell accepts the common vm.tiktok.com and /t/ forms and lets the extractor follow the redirect to the public post. If the redirect lands on a login wall, the download cannot proceed without a session, which Clipwell will not supply.',
          'A profile link is not a video link. Neither is a hashtag page or a search result. Pasting those will produce a “not media” error because there is no single video to analyse. Open the post itself before copying the URL.',
        ],
      },
      {
        heading: 'Why watermark removal is not part of this tool',
        body: [
          'Many downloader sites compete on “no watermark” claims. Clipwell does not. Watermarks are part of the public file and may identify the creator or platform. Removing them is not a neutral technical step, and it can conflict with attribution expectations and platform terms. The tool returns the source as it was served.',
          'The same restraint applies to audio. A TikTok often uses a licensed music track. Being able to extract the audio does not make it royalty-free or safe to upload elsewhere. Check the licence and the platform’s music terms before reusing it.',
        ],
      },
      {
        heading: 'Captions are not the same as the post caption',
        body: [
          'TikTok’s post caption is the text written under the video. Video captions are timed subtitles, often auto-generated. Clipwell can copy the post caption immediately and can load timed subtitles only when the source exposes a track. Mixing those two would make a messy result, so they occupy separate sections.',
          'Auto captions can be wrong, especially with accents, music and overlapping speech. Treat them as a helpful draft. If accuracy matters, review the text before republishing or using it as an accessibility transcript.',
        ],
      },
    ],
  },
  sourceNotes: [
    'App-only posts without a public web view may be unreachable.',
    'Photo carousels and slideshows are not supported.',
    'Watermarks are preserved; Clipwell does not alter attribution.',
  ],
};
