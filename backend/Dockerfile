FROM python:3.12-slim

# No .pyc files, unbuffered stdout (so logs stream to Docker immediately).
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# gosu lets the entrypoint drop from root to the app user after fixing
# volume permissions.
RUN apt-get update \
    && apt-get install -y --no-install-recommends gosu \
    && rm -rf /var/lib/apt/lists/*

# Dependencies first for better layer caching.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# Unprivileged app user + storage mount points.
RUN adduser --system --group --no-create-home appuser \
    && mkdir -p /app/storage/uploads /app/storage/avatars \
    && chown -R appuser:appuser /app

COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
# Strip any CRLF (the file may be edited on Windows) and make executable.
RUN sed -i 's/\r$//' /usr/local/bin/docker-entrypoint.sh \
    && chmod +x /usr/local/bin/docker-entrypoint.sh

EXPOSE 8000

# Container-level liveness (compose/orchestrators read this).
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health').status==200 else 1)"

# Entrypoint fixes volume ownership as root, then execs the CMD as appuser.
# Shell form so ${PORT} is honored — Render injects PORT; locally it's unset
# and defaults to 8000 (which the compose files + healthcheck expect).
#
# --forwarded-allow-ips='*' makes uvicorn trust X-Forwarded-For. Without it,
# request.client.host is the reverse proxy's address (Render's router, or the
# nginx container locally), so the rate limiter buckets every caller together
# under a proxy IP instead of their own — which silently disables brute-force
# protection on login. Trusting '*' is safe here because the app is only ever
# reached through a proxy that overwrites the header at its edge; it must NOT
# be used if the container is ever exposed to the internet directly.
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --forwarded-allow-ips='*'"]
