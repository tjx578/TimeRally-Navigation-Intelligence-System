## Stage 1: build Vite (Node 20 alpine).
FROM node:20-alpine AS build
WORKDIR /app

# Install dependency dulu supaya cache layer-nya stabil.
COPY apps/web-map-console/package*.json ./
RUN npm ci

# Salin semua source termasuk public/ dan .env.production.
COPY apps/web-map-console/ ./

# CATATAN PENTING:
#   Vite memprioritaskan ENV shell di atas file .env.production. Kalau kita set
#   ENV VITE_X="" dari ARG default, build akan mengoverride .env.production yang
#   ditulis oleh redeploy_web.sh -> bundle kosong dari env yang seharusnya berisi.
#
#   Karena itu Dockerfile TIDAK lagi mendeklarasikan ARG/ENV VITE_*. Sumber
#   kebenaran satu-satunya saat build: apps/web-map-console/.env.production
#   yang sudah ada di image stage ini. Operator bisa override per build dengan
#   `gcloud builds submit --substitutions=...` lalu menulis ulang .env.production
#   sebelum docker build (lihat infra/gcp/redeploy_web.sh).
#
#   Kalau benar-benar perlu override per-build, pass via --build-arg dan
#   tambahkan ARG eksplisit untuk variabel itu saja - JANGAN default ke "".

RUN npm run build

## Stage 2: serve via nginx alpine.
FROM nginx:1.27-alpine
COPY apps/web-map-console/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget -qO- http://127.0.0.1:8080/index.html >/dev/null 2>&1 || exit 1
CMD ["nginx", "-g", "daemon off;"]
