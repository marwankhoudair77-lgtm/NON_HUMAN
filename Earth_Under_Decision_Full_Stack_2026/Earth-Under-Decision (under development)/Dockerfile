# Build the approved React/Vite frontend.
FROM node:22-bookworm-slim AS frontend-builder
WORKDIR /build/frontend
COPY frontend/package.json ./package.json
RUN npm install --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

# One deployable service: FastAPI serves both /api and the compiled SPA.
FROM python:3.12-slim AS app-runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FRONTEND_DIST_DIR=/app/frontend_dist \
    LOCAL_STORAGE_ROOT=/app/data \
    PORT=10000
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates libexpat1 \
    && rm -rf /var/lib/apt/lists/*

COPY backend/pyproject.toml /app/backend/pyproject.toml
COPY backend/app /app/backend/app
COPY backend/migrations /app/backend/migrations
COPY backend/alembic.ini /app/backend/alembic.ini
RUN pip install --no-cache-dir /app/backend

COPY --from=frontend-builder /build/frontend/dist /app/frontend_dist
COPY seed_data /app/seed_data
COPY scripts /app/project_scripts
COPY docker/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh && mkdir -p /app/data/raw /app/data/processed

WORKDIR /app/backend
EXPOSE 10000
ENTRYPOINT ["/app/entrypoint.sh"]
