# =============================================================================
# POC-07 -- Retail Inventory Management & Procurement System
# Python image shared by the FastAPI backend and the Streamlit UI.
# =============================================================================
#
# This file did not exist. Both python services in docker-compose.yml declared
# `dockerfile: Dockerfile`, so `docker compose up` failed immediately with
# "failed to read dockerfile" -- the containerised path described in the repo
# docs had never been runnable. One image serves both services; they differ only
# in the `command:` compose passes.

FROM python:3.12-slim

# Python 3.12 rather than the 3.14 used for local development: every dependency
# here publishes manylinux wheels for 3.12, which keeps the image build free of a
# compiler toolchain. Nothing in this codebase uses a 3.13+ language feature.

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app

WORKDIR /app

# curl is needed for the compose healthcheck; build-essential covers any
# dependency that lacks a wheel for this platform. Both layers are removed from
# the final image size by apt cleanup in the same RUN.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl build-essential \
    && rm -rf /var/lib/apt/lists/*

# Requirements are copied and installed before the source so that editing code
# does not invalidate the (slow) dependency layer.
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

# Run as an unprivileged user. The bind mount in docker-compose.yml maps the
# host working tree over /app, and the sqlite database is created inside it, so
# this user must own the directory.
RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000 8501

# Default to the backend; docker-compose.yml overrides this for the Streamlit
# service. Deliberately not --reload: that is a compose-level dev choice.
CMD ["uvicorn", "src.backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
