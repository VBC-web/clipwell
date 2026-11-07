const configuredSite = (import.meta.env.PUBLIC_SITE_URL || 'https://clipwell.app').replace(
  /\/+$/,
  '',
);

export const SITE_URL = configuredSite;
export const DEFAULT_OG_IMAGE = `${SITE_URL}/og/clipwell-og.png`;

export function absoluteUrl(path: string): string {
  if (/^https?:\/\//i.test(path)) return path;
  return `${SITE_URL}${path.startsWith('/') ? path : `/${path}`}`;
}

export interface BreadcrumbItem {
  label: string;
  href?: string;
}

export function breadcrumbJsonLd(items: BreadcrumbItem[]) {
  return {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: items.map((item, index) => ({
      '@type': 'ListItem',
      position: index + 1,
      name: item.label,
      ...(item.href ? { item: absoluteUrl(item.href) } : {}),
    })),
  };
}

export function faqJsonLd(faqs: readonly { question: string; answer: string }[]) {
  return {
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    mainEntity: faqs.map((faq) => ({
      '@type': 'Question',
      name: faq.question,
      acceptedAnswer: {
        '@type': 'Answer',
        text: faq.answer,
      },
    })),
  };
}

export function webApplicationJsonLd(options: {
  name: string;
  description: string;
  path: string;
}) {
  return {
    '@context': 'https://schema.org',
    '@type': 'WebApplication',
    name: options.name,
    description: options.description,
    url: absoluteUrl(options.path),
    applicationCategory: 'MultimediaApplication',
    operatingSystem: 'Any',
    browserRequirements: 'Requires JavaScript for downloads',
    isAccessibleForFree: true,
    offers: {
      '@type': 'Offer',
      price: '0',
      priceCurrency: 'USD',
    },
    provider: {
      '@type': 'Organization',
      name: 'Clipwell',
      url: SITE_URL,
    },
  };
}

export function howToJsonLd(options: {
  name: string;
  description: string;
  steps: readonly { title: string; body: string }[];
}) {
  return {
    '@context': 'https://schema.org',
    '@type': 'HowTo',
    name: options.name,
    description: options.description,
    totalTime: 'PT2M',
    step: options.steps.map((step, index) => ({
      '@type': 'HowToStep',
      position: index + 1,
      name: step.title,
      text: step.body,
    })),
  };
}

export function webPageJsonLd(options: {
  name: string;
  description: string;
  path: string;
  type?: 'WebPage' | 'AboutPage' | 'ContactPage' | 'CollectionPage';
  dateModified?: string;
}) {
  return {
    '@context': 'https://schema.org',
    '@type': options.type || 'WebPage',
    name: options.name,
    description: options.description,
    url: absoluteUrl(options.path),
    inLanguage: 'en',
    isPartOf: {
      '@type': 'WebSite',
      name: 'Clipwell',
      url: SITE_URL,
    },
    ...(options.dateModified ? { dateModified: options.dateModified } : {}),
  };
}
