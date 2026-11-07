import type { APIRoute } from 'astro';
import { SITE_URL } from '../lib/seo';

export const GET: APIRoute = () => {
  const robots = `# Clipwell
User-agent: *
Allow: /
Disallow: /api/

# Download endpoints are not crawlable pages.
User-agent: GPTBot
Allow: /
Disallow: /api/

Sitemap: ${SITE_URL}/sitemap-index.xml
`;

  return new Response(robots, {
    headers: {
      'Content-Type': 'text/plain; charset=utf-8',
      'Cache-Control': 'public, max-age=3600',
    },
  });
};
