import type { PlatformKey } from '../../lib/platforms';

export interface ContentSection {
  heading: string;
  body: string[];
  points?: string[];
}

export interface PlatformContent {
  key: PlatformKey;
  metaTitle: string;
  metaDescription: string;
  eyebrow: string;
  headline: string;
  headlineAccent: string;
  intro: string[];
  glance: string[];
  steps: { title: string; body: string }[];
  features: { title: string; body: string }[];
  problems: { problem: string; solution: string }[];
  faqs: { question: string; answer: string }[];
  article: {
    title: string;
    intro: string;
    sections: ContentSection[];
  };
  sourceNotes: string[];
}
