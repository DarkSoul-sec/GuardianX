# ---- Stage 1: build the React app ----
# Build context is the repository root (see infrastructure/compose/docker-compose.yml).
FROM node:22-alpine AS build

WORKDIR /app

COPY guardianx-frontend/package.json guardianx-frontend/package-lock.json ./
RUN npm ci

COPY guardianx-frontend/ ./
ARG VITE_API_URL=/api
ENV VITE_API_URL=${VITE_API_URL}
RUN npm run build


# ---- Stage 2: serve with nginx ----
FROM nginx:1.27-alpine

COPY --from=build /app/dist /usr/share/nginx/html

# nginx rewrites unknown routes to index.html for client-side routing,
# and proxies /api to the backend container.
COPY infrastructure/docker/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget -qO- http://127.0.0.1/ >/dev/null 2>&1 || exit 1
