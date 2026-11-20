FROM node:20-bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive \
    CHROME_PATH=/usr/bin/chromium \
    PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium

RUN apt-get update \
 && apt-get install -y --no-install-recommends chromium fonts-liberation python3 python3-venv \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN python3 -m venv /opt/venv \
 && /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

COPY ["Marp Vorlage von Rea/package.json", "Marp Vorlage von Rea/package-lock.json", "./"]
RUN npm ci --omit=dev

COPY ["Marp Vorlage von Rea/input", "./input"]
COPY ["Marp Vorlage von Rea/imgs", "./imgs"]
COPY Theme/ ./Theme/
COPY Scripts/ ./Scripts/
COPY Modules/ ./Modules/
COPY Courses/ ./Courses/
COPY Assets/ ./Assets/

RUN mkdir -p /app/output /app/build \
 && chown -R node:node /app

ENV PATH="/opt/venv/bin:/app/node_modules/.bin:${PATH}"
USER node

ENTRYPOINT ["marp"]
CMD ["--help"]
