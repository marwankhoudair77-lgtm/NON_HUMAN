#!/bin/sh
set -eu

: "${LOCAL_STORAGE_ROOT:=/app/data}"
: "${PORT:=10000}"
export LOCAL_STORAGE_ROOT PORT

mkdir -p "$LOCAL_STORAGE_ROOT/raw" "$LOCAL_STORAGE_ROOT/processed" "$LOCAL_STORAGE_ROOT/staging" "$LOCAL_STORAGE_ROOT/exports" "$LOCAL_STORAGE_ROOT/tmp"

# Seed the persistent data volume only with files that do not already exist.
# This preserves user uploads and never overwrites an existing original.
if [ -d /app/seed_data ]; then
  cp -an /app/seed_data/. "$LOCAL_STORAGE_ROOT/"
fi

# Wait for Postgres before applying versioned migrations.
if [ -n "${DATABASE_URL:-}" ]; then
  attempt=0
  until python -c 'from sqlalchemy import create_engine, text; from app.core.config import get_settings; engine=create_engine(get_settings().database_url); connection=engine.connect(); connection.execute(text("SELECT 1")); connection.close(); engine.dispose()' >/dev/null 2>&1; do
    attempt=$((attempt + 1))
    if [ "$attempt" -ge 60 ]; then
      echo "Database did not become ready after 120 seconds; refusing to start without migrations." >&2
      exit 1
    fi
    echo "Waiting for PostgreSQL ($attempt/60)..."
    sleep 2
  done
  alembic upgrade head
fi

exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
