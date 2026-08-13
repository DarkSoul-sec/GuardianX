# ---- Stage 1: build dependencies ----
FROM python:3.13-slim AS builder

WORKDIR /app

# Compile-time dependencies for psycopg binary wheels and cryptography.
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ---- Stage 2: runtime ----
FROM python:3.13-slim AS runtime

# nmap is required by the scan engine.
RUN apt-get update \
    && apt-get install -y --no-install-recommends nmap curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10001 guardianx

WORKDIR /app

COPY --from=builder /install /usr/local

COPY alembic.ini .
COPY alembic ./alembic
COPY app ./app

USER guardianx

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD curl -fsS http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]