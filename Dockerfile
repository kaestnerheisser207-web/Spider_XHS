FROM python:3.10-slim

ARG XHS_SERVICE_REVISION=unknown

LABEL org.opencontainers.image.title="Spider_XHS Service" \
      org.opencontainers.image.revision="${XHS_SERVICE_REVISION}"

WORKDIR /app

RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

RUN python --version && node --version && npm --version

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY package.json package-lock.json ./

RUN npm ci --omit=dev --ignore-scripts \
    && npm cache clean --force

COPY . .

RUN groupadd --gid 10001 xhs \
    && useradd --uid 10001 --gid 10001 --no-create-home --shell /usr/sbin/nologin xhs

EXPOSE 5000

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV NODE_ENV=production

USER 10001:10001

HEALTHCHECK --interval=10s --timeout=3s --start-period=20s --retries=3 \
    CMD curl --fail --silent http://127.0.0.1:5000/healthz || exit 1

# One worker owns the in-memory login and authenticated HTTP sessions. Scaling
# uses one container per worker rather than Uvicorn's multi-worker mode.
CMD ["uvicorn", "xhs_service.app:app", "--host", "0.0.0.0", "--port", "5000", "--no-access-log"]
