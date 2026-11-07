import type { PlatformContent } from './types';

export const instagram: PlatformContent = {
  key: 'instagram',
  metaTitle: 'Instagram Video Downloader — Save Public Reels | Clipwell',
  metaDescription:
    'Download public Instagram Reels, feed videos and IGTV in the qualities Instagram exposes. Save audio and captions when available. No login, no private posts.',
  eyebrow: 'Instagram downloader',
  headline: 'Save the Reels',
  headlineAccent: 'worth keeping.',
  intro: [
    'Instagram makes it easy to watch a clip and strangely hard to keep it. Clipwell takes a public Reel, feed video or IGTV link, reads the available formats, and puts the useful details in one place: title, creator, duration, description, caption tracks and download options.',
    'No login, no browser extension and no guessing which resolution will arrive. If Instagram only exposes one stream for a post, that is the only option you will see. If the post is private, removed or not actually a video, Clipwell says so instead of spinning a progress bar forever.',
  ],
  glance: [
    'Public Reels, feed videos and IGTV posts',
    'MP4 downloads in the resolutions Instagram provides',
    'Description and caption access when the post exposes them',
  ],
  steps: [
    {
      title: 'Copy the post link, not the profile link',
      body: 'Open the public post in Instagram, tap the three-dot menu and choose Copy link. A reel link usually looks like instagram.com/reel/ followed by a short code. Profile and story links will be rejected because they do not point to one downloadable video.',
    },
    {
      title: 'Paste it into the field above',
      body: 'Clipwell checks the hostname and confirms it is an Instagram media URL before contacting the backend. If you accidentally paste a link from another platform, you will get a suggestion for the correct downloader.',
    },
    {
      title: 'Pick a real format and save',
      body: 'The results panel lists only the streams Instagram returned. Choose a video quality or an audio option, then start the download. Temporary files are deleted shortly after the job finishes or expires.',
    },
  ],
  features: [
    {
      title: 'Reels, videos and IGTV in one tool',
      body: 'The extractor follows the post type rather than asking you to choose a separate mode. A public Reel and a longer feed video are handled by the same input.',
    },
    {
      title: 'Details before the download',
      body: 'See the creator, post text, duration and thumbnail before committing to a file. The description has its own copy button so you can keep context without copying the whole page.',
    },
    {
      title: 'Captions when Instagram offers them',
      body: 'Available caption tracks can be loaded as readable text and downloaded as SRT or TXT. Instagram does not provide captions for every post, so the panel stays empty rather than fabricating a transcript.',
    },
    {
      title: 'Audio-only when there is audio',
      body: 'If the post has a usable audio stream, Clipwell can produce an MP3 or an original M4A. The options are tied to the actual media, not to a generic menu.',
    },
  ],
  problems: [
    {
      problem: '“This content isn’t available” or a login screen appears',
      solution:
        'The post is probably private, age-restricted, deleted or limited to logged-in accounts. Clipwell cannot sign in or bypass that restriction. Try a post that opens normally in a private browser window.',
    },
    {
      problem: 'The link looks valid but no formats are returned',
      solution:
        'Photo carousels and image posts do not contain a downloadable video. Multi-video carousels may expose one video entry at a time. Open the exact reel or video from the carousel and copy its direct link.',
    },
    {
      problem: 'The page keeps asking you to open the app',
      solution:
        'Use Instagram’s Copy link action instead of copying the address from the app’s browser preview. Short share URLs are supported, but the link still needs to point at a public post.',
    },
  ],
  faqs: [
    {
      question: 'Can I download from a private Instagram account?',
      answer:
        'No. Clipwell only accepts public media and never asks for Instagram credentials or cookies. Private accounts, close friends posts, login-only reels and stories are outside what the service can or should access.',
    },
    {
      question: 'Does it download every video in a carousel?',
      answer:
        'Not necessarily. Instagram carousels can contain mixed media, and the public metadata may describe only one video entry. Clipwell reports what the public post exposes rather than pretending to unpack the whole carousel.',
    },
    {
      question: 'Will the Instagram audio be included?',
      answer:
        'Video downloads include the audio stream when the platform provides one. For music-heavy reels, the available audio may be tied to the video stream. Clipwell does not circumvent licensing or extract audio that Instagram does not expose.',
    },
    {
      question: 'Can I save the caption text as a subtitle file?',
      answer:
        'You can copy the post description at any time. If Instagram exposes subtitle tracks for the video, Clipwell can load them and let you download SRT or plain text. These are video captions, not the caption you write under a post.',
    },
    {
      question: 'Is downloading an Instagram Reel legal?',
      answer:
        'It depends on why you are downloading it and where you live. Save your own posts or media you have permission to use. Public visibility does not grant reuse rights, so do not republish someone else’s video without a licence or a valid legal exception.',
    },
  ],
  article: {
    title: 'How to download an Instagram Reel without copying the wrong link',
    intro:
      'Most failed Instagram downloads start with the wrong URL. Instagram has profile links, post links, story links, highlight links and app share links, and only some of them identify a single public video. Knowing which one you have saves a lot of trial and error.',
    sections: [
      {
        heading: 'What a useful Instagram link contains',
        body: [
          'A public Reel link includes a short post code after /reel/, /reels/ or /p/. A feed video uses /p/ or /tv/. Share links created by the app can use a different path and then redirect, which is why Clipwell accepts the common public share forms rather than insisting on one exact URL shape.',
          'The distinction matters because Clipwell works on one post at a time. A profile URL does not say which video you mean. A story URL may only be available to a logged-in viewer. Selecting Copy link from the individual post is the most reliable route.',
        ],
      },
      {
        heading: 'Why Clipwell shows a limited quality list',
        body: [
          'Instagram controls the renditions it publishes for each video. Some posts are served at a single resolution; others expose a few. Clipwell reads the public formats and builds the menu from those entries. It does not upscale a 720p source to 4K or label a re-encoded file as “original” when it is not.',
          'For most reels, a single MP4 is the honest outcome. That is not a limitation of the interface; it reflects the source. The format note beside each option tells you the resolution and estimated size when the platform supplies them.',
        ],
      },
      {
        heading: 'A note on ownership and captions',
        body: [
          'Downloading your own reel is a sensible way to keep an archive. Downloading someone else’s video is only appropriate when you have permission or a legal exception. Clipwell is a technical tool; it does not grant rights to the material.',
          'The post description and any subtitle tracks serve different purposes. The description is the text the creator wrote under the post, while captions are timed text attached to the video. Clipwell keeps those separate so you can copy the context without confusing it with a transcript.',
        ],
      },
    ],
  },
  sourceNotes: [
    'Instagram may require a login for some posts even when they appear public in a preview.',
    'Stories, highlights and private accounts are intentionally unsupported.',
    'Quality choices are limited to the renditions Instagram actually serves.',
  ],
};
