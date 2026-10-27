FROM node:20-bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive \
    CHROME_PATH=/usr/bin/chromium \
    PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium

RUN apt-get update \
 && apt-get install -y --no-install-recommends chromium fonts-liberation \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY ["Marp Vorlage von Rea/package.json", "Marp Vorlage von Rea/package-lock.json", "./"]
RUN npm ci --omit=dev

COPY ["Marp Vorlage von Rea/input", "./input"]
COPY ["Marp Vorlage von Rea/imgs", "./imgs"]
COPY ["Marp Vorlage von Rea/theme", "./theme"]

RUN mkdir -p /app/output \
 && chown -R node:node /app

ENV PATH="/app/node_modules/.bin:${PATH}"
USER node

ENTRYPOINT ["marp"]
CMD ["--help"]
