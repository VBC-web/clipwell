import type { PlatformContent } from './types';

export const twitter: PlatformContent = {
  key: 'twitter',
  metaTitle: 'X (Twitter) Video Downloader — Save Public Post Video | Clipwell',
  metaDescription:
    'Download native video from public X (Twitter) posts in the qualities X exposes. Copy post text and captions when available. Private posts, Spaces and live video are unsupported.',
  eyebrow: 'X downloader',
  headline: 'From the post,',
  headlineAccent: 'not the timeline.',
  intro: [
    'X posts can contain more than one video, a mix of images and clips, or a video embedded beside a long thread. Clipwell starts from one direct post URL, extracts the native video the post exposes and shows the available renditions before you download.',
    'The tool works only with public posts. Protected accounts, subscriber-only posts, Spaces and live video are not supported. Post text, author, duration and caption tracks are displayed alongside the media so the file keeps its context when you archive it.',
  ],
  glance: [
    'Public X posts containing native video',
    'Available MP4 renditions and source details',
    'Post text and caption access when exposed',
  ],
  steps: [
    {
      title: 'Copy the post’s direct URL',
      body: 'Open the post and use Copy link. A direct status URL contains /status/ and a numeric ID. Profile pages, search results, threads without a selected post and t.co redirects from another app are not reliable inputs.',
    },
    {
      title: 'Paste it above',
      body: 'Clipwell checks that the host is x.com or twitter.com and that the path identifies a status. A link from any other platform is rejected with a suggestion for the right downloader.',
    },
    {
      title: 'Pick the video, not the whole thread',
      body: 'One post can expose one or more video entries, but the download panel focuses on the media attached to the status you submitted. Choose an available quality and save the file.',
    },
  ],
  features: [
    {
      title: 'Both X and Twitter domains',
      body: 'Old twitter.com links and current x.com links are accepted. You do not need to rewrite a shared URL before using the downloader.',
    },
    {
      title: 'Post context stays attached',
      body: 'The author, post text and media details are displayed together. Copy the text separately when you need the source context for research or an archive.',
    },
    {
      title: 'Native video only',
      body: 'Clipwell is not a timeline scraper. It processes the video attached to the status URL you provide, not every post from an account.',
    },
    {
      title: 'Captions when X provides them',
      body: 'Some posts include subtitle tracks; many do not. Available tracks can be copied as text or downloaded as SRT. The tool never presents a guessed transcript as a real caption file.',
    },
  ],
  problems: [
    {
      problem: 'The post has video but no formats appear',
      solution:
        'The video may be a live broadcast, a Spaces recording, or media that requires a logged-in viewer. X also changes its media pipeline periodically. Confirm the post opens publicly and contains native video, then retry.',
    },
    {
      problem: 'You pasted a t.co short link',
      solution:
        't.co links can redirect outside X and are not accepted by the backend for safety. Open the link in a browser, then copy the final x.com/username/status/… address and paste that instead.',
    },
    {
      problem: 'Multiple videos in one post are handled inconsistently',
      solution:
        'Clipwell extracts the media entry the public post exposes. If a post contains several videos, use the direct post URL and check the result title and thumbnail before downloading. The service does not create a multi-file archive from one post.',
    },
  ],
  faqs: [
    {
      question: 'Does Clipwell work with both x.com and twitter.com?',
      answer:
        'Yes. Both domains are recognised, including mobile and www subdomains. The detector treats them as the same platform and keeps any query parameters needed to resolve the post.',
    },
    {
      question: 'Can I download video from a protected X account?',
      answer:
        'No. Protected posts require an authenticated follower relationship. Clipwell does not accept cookies or sign in on your behalf. Only posts that are publicly accessible to anonymous requests can be processed.',
    },
    {
      question: 'Are Spaces or live videos supported?',
      answer:
        'No. Spaces are audio-first broadcasts and live video is not a finished file. Clipwell handles native video attached to a public post. Ended live replays may be treated like ordinary video if X exposes them that way, but recording is not supported.',
    },
    {
      question: 'Can I copy the post text without downloading the video?',
      answer:
        'Yes. The description section shows the public post text with its own copy button. You can use it without starting a download. The text is whatever the public page returned at extraction time.',
    },
    {
      question: 'Why do some X videos have only one quality?',
      answer:
        'X often serves a small set of MP4 renditions, and some posts expose only one. Clipwell lists what is available and does not remux a second file just to create the appearance of choice.',
    },
  ],
  article: {
    title: 'Saving video from X: direct status links, not screenshots of the timeline',
    intro:
      'The most common X downloader mistake is feeding it a profile or a search page. Those pages contain many posts and no single answer to “which video?” A direct status link identifies one post, which is exactly what a media extractor needs.',
    sections: [
      {
        heading: 'What a direct status URL looks like',
        body: [
          'A status URL contains a username, the word status and a numeric post ID, for example x.com/username/status/1234567890. The older twitter.com domain uses the same structure. Mobile share sheets may produce a t.co link first; that redirect can land anywhere, so Clipwell rejects it and asks for the expanded URL.',
          'If the post is part of a thread, copy the link from the specific post containing the video rather than the first post in the thread. The extractor uses the status you provide and does not assume the media belongs to the opening post.',
        ],
      },
      {
        heading: 'Multiple videos and mixed media',
        body: [
          'Some posts attach more than one video, while others combine images with a single clip. The public metadata may expose one primary media entry or several. Clipwell shows the result it can verify and keeps the download focused on that entry. It does not silently zip a whole thread.',
          'This is also why the title and thumbnail matter. Check them against the post you meant to save. A successful request for the wrong video is worse than a clear error.',
        ],
      },
      {
        heading: 'Copyright and context travel with the file',
        body: [
          'A public post is not a licence to reuse its video. News footage, sports clips, music videos and other people’s creative work remain protected. Save what you own, what you have permission to use, or what falls under a valid exception in your jurisdiction.',
          'Clipwell shows the post text and author so you can keep attribution attached to an archive. If you republish the clip, verify the rights and follow X’s terms. The downloader provides a file, not legal cover.',
        ],
      },
    ],
  },
  sourceNotes: [
    'Protected accounts and subscriber-only posts are unsupported.',
    'Spaces and live video are not recorded.',
    't.co short links are rejected; use the expanded status URL.',
  ],
};
