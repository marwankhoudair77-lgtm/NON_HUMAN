# Release manifest — Earth Under Decision

Release bundle: `Earth_Under_Decision_Full_Stack_2026.zip`

Included:
- Approved React + TypeScript + Vite frontend, connected to the FastAPI API.
- FastAPI modular backend, SQLAlchemy models, Alembic migrations, and PostgreSQL/PostGIS configuration.
- Uploaded 2023 raw data under `seed_data/raw/`.
- Uploaded cleaned outputs under `seed_data/processed/`.
- Adapted reproducible cleaning script and unchanged copy of the user-uploaded cleaning script.
- Placeholder-only `.env` and `.env.example`; no private credentials.
- Docker Compose stack and Windows double-click START / STOP / VIEW LOGS scripts.
- Render Blueprint and Arabic deployment guide.

Data notes:
- GLDAS Noah 2.1: 365 daily records at one model grid point.
- GPM_3IMERGM v07: 540 valid 0.1-degree grid cells; time-mean rate with annualized-equivalent display.
- NOAA GHCN-Daily: external comparison reference, not NASA.
- MOD13Q1 NDVI and MOD11A2 LST files were not provided and are not fabricated.

Validation performed in the build environment:
- 12 Python tests passed.
- Alembic migrations applied to SQLite for structural verification.
- Uploaded cleaned CSV outputs were reproduced byte-identically by `scripts/clean_data.py`.
- TypeScript/TSX syntax parsing passed for the application entry files.
- Docker build and full Vite production build were not run here because Docker was unavailable and npm registry network access failed.
- No cloud service was created or deployed; the included `render.yaml` is a deployment blueprint for the user's account.
