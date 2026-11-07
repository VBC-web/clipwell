# syntax=docker/dockerfile:1
FROM node:22-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund

COPY . .

# These are build-time values. The empty API base means "same origin", which is
# what the bundled Nginx config expects when it proxies /api/ to the backend.
ARG PUBLIC_SITE_URL=https://clipwell.app
ARG PUBLIC_API_BASE_URL=""
ENV PUBLIC_SITE_URL=$PUBLIC_SITE_URL \
    PUBLIC_API_BASE_URL=$PUBLIC_API_BASE_URL

RUN npm run build

FROM nginx:alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -q -O /dev/null http://127.0.0.1/ || exit 1
