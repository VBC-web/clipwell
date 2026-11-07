import type { PlatformContent } from './types';

export const facebook: PlatformContent = {
  key: 'facebook',
  metaTitle: 'Facebook Video Downloader — Save Public Videos | Clipwell',
  metaDescription:
    'Download public Facebook videos, Reels and Watch posts in the qualities Facebook provides. Copy descriptions and captions when available. Public links only.',
  eyebrow: 'Facebook downloader',
  headline: 'Out of the feed,',
  headlineAccent: 'into your files.',
  intro: [
    'Facebook videos arrive through a maze of URL shapes: Watch pages, page videos, reel links, share links and the occasional fb.watch shortcut. Clipwell resolves the public link you have, asks the source what formats exist, and presents a single download panel without the surrounding feed.',
    'This tool is built for public posts you can open without signing in. Group videos, friends-only posts and anything that requires a session are not supported. When Facebook refuses a link, Clipwell explains the likely reason rather than returning an empty download list.',
  ],
  glance: [
    'Public Watch videos, page videos and Reels',
    'Video qualities tied to the source renditions',
    'Post text and captions when Facebook exposes them',
  ],
  steps: [
    {
      title: 'Get the video’s own link',
      body: 'On the public post, open the menu and choose Copy link. If the video is inside a page post, open it first so the URL identifies the video rather than the page. The fb.watch shortcut is also accepted when it resolves to public content.',
    },
    {
      title: 'Let Clipwell identify the source',
      body: 'The URL is checked before any fetch is attempted. A YouTube or Instagram URL pasted here will be detected and redirected to the matching downloader with the link preserved.',
    },
    {
      title: 'Review the post details, then download',
      body: 'Check the thumbnail, publisher, duration and available renditions. Pick a video quality or audio stream that is actually listed. The download job reports its progress and can be retried if the platform temporarily refuses the request.',
    },
  ],
  features: [
    {
      title: 'Handles common Facebook URL forms',
      body: 'Watch links, /videos/ links, reels, story-style video URLs and fb.watch shortcuts are recognised, so you do not have to translate the link by hand.',
    },
    {
      title: 'No feed, no autoplay',
      body: 'The result view is focused on one public post. You get the media details and format list without loading Facebook’s recommendation engine around the video.',
    },
    {
      title: 'Description and caption tools',
      body: 'Copy the post text for context or save an available subtitle track as SRT or TXT. If the uploader did not provide captions and Facebook has not generated any, the interface says they are unavailable.',
    },
    {
      title: 'Temporary processing',
      body: 'The backend writes the selected file to a short-lived job directory, serves it, and removes it on the cleanup schedule. It is not a permanent media archive.',
    },
  ],
  problems: [
    {
      problem: 'The video opens for you but Clipwell says it cannot access it',
      solution:
        'The post may be visible because of your Facebook session but not public to anonymous requests. Log out or use a private window to confirm. Clipwell deliberately does not accept session cookies, so login-only posts will fail.',
    },
    {
      problem: 'Only a low-resolution format is listed',
      solution:
        'Facebook may expose only one progressive file for a post, especially for older uploads or reels. Clipwell does not invent an HD version. Try downloading the original-quality option if it appears; otherwise the available stream is the source’s limit.',
    },
    {
      problem: 'A page URL keeps returning “not a video”',
      solution:
        'Copy the link from the individual video post, not the page’s main timeline. Page URLs can contain many posts and do not identify a single downloadable video.',
    },
  ],
  faqs: [
    {
      question: 'Can Clipwell download videos from private Facebook groups?',
      answer:
        'No. Group content is often private or membership-only, and Clipwell does not authenticate as you. Only links that resolve as public media are accepted. Public group posts may still be refused if Facebook requires a login to serve them.',
    },
    {
      question: 'Does it support Facebook Reels as well as Watch videos?',
      answer:
        'Yes, public Reels are supported alongside Watch links and standard page videos. The interface detects the post type from the URL and the metadata returned by the platform, not from a manual “reel” toggle.',
    },
    {
      question: 'Why does a Facebook link have so many query parameters?',
      answer:
        'Facebook adds tracking and routing parameters to shared links. Clipwell accepts the URL as shared, validates the hostname and asks the extractor to resolve the video. You do not need to remove the parameters yourself.',
    },
    {
      question: 'Can I download a live Facebook broadcast?',
      answer:
        'An active live stream is not a finished file and is not offered here. If the broadcast has ended and Facebook exposes a replay, the replay link may work. Clipwell does not record or monitor live sessions.',
    },
    {
      question: 'Is the Facebook video quality guaranteed?',
      answer:
        'No. The available formats are whatever Facebook serves to an anonymous request for that post. Quality can vary by upload, region and platform changes. The menu only lists renditions that were present at extraction time.',
    },
  ],
  article: {
    title: 'Why Facebook video links fail, and how to pick a better one',
    intro:
      'Facebook is not one product. A link can point to a Watch episode, a page video, a reel, a group post or a shortened share URL. The same Copy link button can produce very different URLs depending on where you tapped it. Clipwell handles the public forms it can verify and explains the rest.',
    sections: [
      {
        heading: 'Open the individual video first',
        body: [
          'If you are on a page’s feed, the address bar may refer to the page rather than the video that is playing. Open the post in its own view, then copy the URL. You can also use the post menu, which usually gives a link with the video identifier included.',
          'The fb.watch domain is a shortcut service. Clipwell accepts it, but the resulting public page still has to expose the media. A shortcut to a private group video will fail for the same reason the original URL would.',
        ],
      },
      {
        heading: 'What “available qualities” really means',
        body: [
          'Facebook often serves a single progressive MP4 for a public video, though some posts expose separate audio and video streams. Clipwell builds its list from the extractor’s view of the post. If the platform only provides one file, an interface that offered 4K anyway would be lying.',
          'The download is processed as an MP4 when the source streams can be combined cleanly. FFmpeg handles the merge, while the selected resolution remains bounded by the highest available source stream.',
        ],
      },
      {
        heading: 'Public availability can change',
        body: [
          'A post that was public yesterday can be made private, deleted or restricted today. A downloader cannot cache a permission you no longer have. If the link suddenly stops working, check whether it still opens in a private browser window before assuming the tool is broken.',
          'Captions are equally dependent on the source. Facebook generates captions for some videos and lets creators upload their own for others. When neither exists, Clipwell keeps the caption section honest and empty.',
        ],
      },
    ],
  },
  sourceNotes: [
    'Private groups, friends-only posts and login walls are not supported.',
    'Active live broadcasts cannot be saved; replays may be available.',
    'Some older or Reels uploads expose only one progressive rendition.',
  ],
};
