# ToolNest Backend Dockerfile for Render Free Web Service
# Uses pinned official Astral uv multi-stage build

FROM ghcr.io/astral-sh/uv:0.12.10 AS uv

FROM python:3.12-slim-bookworm

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    PATH="/app/.venv/bin:$PATH"

# Copy uv executable from official image
COPY --from=uv /uv /uvx /bin/

# Copy dependency specifications first for optimal layer caching
COPY pyproject.toml uv.lock ./

# Install production dependencies using frozen lockfile
RUN uv sync --frozen --no-dev --no-install-project

# Copy application source code, static site builder, and migrations
COPY app/ app/
COPY migrations/ migrations/
COPY scripts/ scripts/
COPY site_builder/ site_builder/
COPY alembic.ini .
COPY README.md .

# Render injects PORT environment variable dynamically (default 8000)
EXPOSE 8000

# Execute with uvicorn listening on 0.0.0.0 and platform-provided PORT
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

