import type { PlatformKey } from '../../lib/platforms';
import { facebook } from './facebook';
import { instagram } from './instagram';
import { kick } from './kick';
import { tiktok } from './tiktok';
import { twitch } from './twitch';
import { twitter } from './twitter';
import type { PlatformContent } from './types';
import { youtube } from './youtube';

export type { ContentSection, PlatformContent } from './types';

export const PLATFORM_CONTENT: Record<PlatformKey, PlatformContent> = {
  instagram,
  facebook,
  youtube,
  tiktok,
  kick,
  twitch,
  twitter,
};

export const PLATFORM_CONTENT_LIST = [
  facebook,
  instagram,
  youtube,
  tiktok,
  kick,
  twitch,
  twitter,
];
