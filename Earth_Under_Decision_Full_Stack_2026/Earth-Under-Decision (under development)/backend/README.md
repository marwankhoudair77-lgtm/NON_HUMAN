# Earth Under Decision — Backend

Backend and uploaded-story-data API for **Earth Under Decision** (Team NON-HUMAN), built from the uploaded Backend Master Prompt and the received cleaning/data package.

## Implemented

- FastAPI application, `/health`, `/ready`, Swagger docs at `/docs` and ReDoc at `/redoc`.
- Versioned API routes for indicators, sources, datasets, study areas, uploaded assets, jobs, dashboard summary, trends, comparisons, map layers, and scenarios.
- PostgreSQL/PostGIS-oriented SQLAlchemy schema and Alembic baseline migration.
- Candidate-only records for `MOD13Q1.061` and `MOD11A2.061`; these products are not yet uploaded. The supplied GPM file is catalogued separately as `GPM_3IMERGM` v07 Monthly time-mean precipitation-rate data.
- Candidate study-area hierarchy for Global Context → Egypt → Nile Delta → Gharbia / Kafr El-Sheikh / Sharqia; there are no guessed polygons or coordinates in the database.
- Protected manual upload for GeoTIFF, HDF4/HDF5, and NetCDF signatures.
- Streaming upload, size enforcement, SHA-256, duplicate detection, generated storage keys, safe path resolution, raw/processed directory separation, and no filesystem paths in API responses.
- Metadata inspection through Rasterio, h5py, Xarray/h5netcdf, and optional PyHDF for HDF4 files.
- Metadata/format inspection does **not** mark an asset scientifically validated. All uploaded assets remain pending scientific validation until product-specific checks are implemented and run.
- Explicit no-data responses for trends and map layers rather than invented observations.
- Theil–Sen/Kendall trend helper with a minimum sample threshold and descriptive-only default; it is covered by synthetic unit tests and is not yet exposed as a scientific inference endpoint.
- What-If assumptions can be stored as `illustrative_only`; no environmental forecast is calculated.
- CORS allow-list and bearer-token protection on administrative ingestion/upload/processing operations.
- Storytelling endpoints serve the processed GLDAS daily/monthly series, GPM grid-cell GeoJSON, real data inventory, QA summary, source catalog, and limitations.
- Frontend Dashboard, Explore Map, Trend/Seasonal Profile, and Methodology pages consume these real storytelling endpoints; NOAA stays a separately labeled external reference.
- A root Dockerfile and Compose setup build the Vite app and serve it from FastAPI on the same origin. `render.yaml` is prepared for a GUI Blueprint deployment with PostgreSQL and a persistent data disk.

## Explicitly pending — not claimed as complete

- NASA AppEEARS and GES DISC automatic acquisition adapters. The adapter interface exists, but connectors remain pending official API/auth/request/download verification.
- Product-specific QA masks, scale factors, fill values, units, and transformations for real MODIS/GPM assets.
- Validated official administrative geometries for Egypt and the selected Nile Delta pilot area.
- Cleaning/aggregation/reprojection pipeline and reproducible processing-run execution.
- Background worker for long processing jobs.
- COG generation and real raster tile delivery.
- Scientific inference endpoints that calculate trend statistics from validated assets.
- Scenario calculation models.
- Browser/admin upload UI. Manual upload is currently an authorized API operation; the admin token must never be exposed to browser code.
- Browser-level end-to-end test and full frontend production build. Dependency installation timed out in the build environment, so the TypeScript/Vite build could not be completed here.

The supplied NASA-derived data files are included as read-only seed assets under `seed_data/` for the deployed storytelling views. They are **not** labeled scientifically validated. No statistical-significance findings or validated administrative boundaries are seeded, and no NASA automatic-download event is claimed.

## API route summary

| Method | Route | Current behavior |
|---|---|---|
| GET | `/health` | API liveness |
| GET | `/ready` | DB + PostGIS readiness (503 when unavailable) |
| GET | `/api/v1/indicators` | NDVI / LST / precipitation definitions |
| GET | `/api/v1/data-sources` | Candidate source connector metadata |
| GET | `/api/v1/datasets` | Candidate product catalog and verification status |
| GET | `/api/v1/datasets/{dataset_id}` | Product metadata |
| GET | `/api/v1/study-areas` | Candidate / validated study areas |
| GET | `/api/v1/study-areas/{area_id}` | Area metadata, no internal filesystem data |
| POST | `/api/v1/data-assets/upload` | Protected manual raw-file upload and metadata inspection |
| GET | `/api/v1/data-assets` | Safe asset metadata list |
| GET | `/api/v1/data-assets/{asset_id}` | Safe asset metadata detail |
| POST | `/api/v1/ingestion/jobs` | Explicit 501 until a verified source connector exists; no fake job |
| GET | `/api/v1/jobs/{job_id}` | Persistent job status lookup |
| POST | `/api/v1/jobs/{job_id}/cancel` | Protected cancellation of queued jobs |
| POST | `/api/v1/processing/jobs` | Explicit 501 until product QA and a worker exist |
| GET | `/api/v1/processing/jobs/{job_id}` | Processing-job status lookup |
| GET | `/api/v1/processing/runs/{run_id}` | Processing provenance lookup |
| GET | `/api/v1/dashboard/summary` | Real catalog/asset/layer counts; no fabricated science metrics |
| GET | `/api/v1/trends` | Completed-run time series only; unavailable when absent |
| GET | `/api/v1/comparisons` | Explicit unavailable response until validated data/boundaries exist |
| GET | `/api/v1/analysis/runs/{run_id}` | Stored analysis run and its results |
| GET | `/api/v1/analysis/results/{result_id}` | Stored analysis result |
| GET | `/api/v1/maps/layers` | Only scientifically validated and available layers |
| GET | `/api/v1/maps/layers/{layer_id}` | Validated layer metadata |
| POST | `/api/v1/scenarios` | Stores assumptions as illustrative only |
| GET | `/api/v1/scenarios/{scenario_id}` | Stored assumptions and status |
| GET | `/api/v1/scenarios/{scenario_id}/results` | No result/forecast until a validated model exists |

## Prerequisites

- Python 3.11+ (Docker image uses Python 3.12).
- Docker Desktop / Docker Engine with Compose for PostgreSQL/PostGIS.
- Node.js 20+ for the frontend.

## Setup

1. From the repository root, copy `.env.example` to `.env`.
2. Change `POSTGRES_PASSWORD` and make the password in `DATABASE_URL` match it. Set a long random `ADMIN_API_TOKEN` in `.env`. Do not send credentials in chat or commit `.env`.
3. Start the PostGIS database:

   ```bash
   docker compose up -d db
   ```

4. Create and activate a Python environment:

   ```bash
   cd backend
   python -m venv .venv
   # Windows PowerShell: .venv\Scripts\Activate.ps1
   # macOS/Linux: source .venv/bin/activate
   pip install -e '.[test]'
   ```

5. Optional: install HDF4 metadata support for MODIS-style HDF4 files. This requires compatible system HDF4 libraries as well as PyHDF:

   ```bash
   pip install -e '.[hdf4]'
   ```

   Without the optional reader, HDF4 uploads are preserved but metadata review remains pending.

6. Apply the migration and run the API:

   ```bash
   alembic upgrade head
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

7. Open `http://localhost:8000/docs`; check `http://localhost:8000/health` and `http://localhost:8000/ready`.

## Frontend

The approved React/Vite project remains in `frontend/`:

```bash
cd frontend
npm install
npm run dev
```

`frontend/.env.example` contains only `VITE_API_BASE_URL=http://localhost:8000`. Never put the admin token, NASA credentials, database passwords, or storage keys in any `VITE_` variable.

## Manual upload

`POST /api/v1/data-assets/upload` requires:

- `multipart/form-data` field `file`.
- Optional `dataset_id`, `source_id`, and `operator_notes`.
- `Authorization: Bearer <ADMIN_API_TOKEN>` header.

Supported extension/signature combinations are checked. The untouched original is stored under `data/raw/` and registered with a SHA-256 checksum. The API deliberately does not mark it scientifically validated. Product version, QA bands/flags, scale/offset, units, temporal coverage, NoData handling, and provenance must still be reviewed.

## Important behavior

- Automatic acquisition returns an explicit pending/not-implemented response rather than simulating a NASA download.
- Product processing returns an explicit pending/not-implemented response until valid product-specific QA rules and a worker are configured.
- Trend API data comes only from stored completed analysis runs; an empty result is clearly `unavailable`.
- Map API data comes only from layers linked to assets marked scientifically validated.
- Scenarios save assumptions only; outputs remain `illustrative_only`, not predictions.
- Local storage is implemented behind a storage factory. S3-compatible storage is an extension point, not implemented in this delivery.

## Tests executed in the build environment

From `backend/`:

```bash
pip install -e '.[test]'
pytest
```

Tests use synthetic fixtures only. They are not project observations and are never inserted into the candidate data catalog.

The current build environment did not provide Docker or a running PostgreSQL/PostGIS service. Alembic was successfully applied to SQLite as a structural smoke test, and the Python test suite passed (12 tests). **This is not a substitute for the first migration against PostgreSQL/PostGIS.** The Vite dependency install/build also could not be completed in this environment because the npm registry was unreachable.


## Uploaded 2023 dataset integration

The received files are preserved under `seed_data/raw/`; the processed outputs and `qc_report_2023.json` are under `seed_data/processed/`. At container startup, files are copied into the persistent `LOCAL_STORAGE_ROOT` only when a destination file does not already exist. This avoids overwriting later user uploads.

- GLDAS Noah 2.1 3-hourly exports: 365 daily rows at one model grid point, exactly eight source steps per day. ET is interpreted as modelled natural-condition response, not actual irrigated agriculture water consumption.
- GPM `GPM_3IMERGM` v07: 540 valid 0.1-degree cells from a time-mean rate raster in mm/hr. The annualized equivalent shown in the map is derived from that rate, not a direct daily accumulation total.
- NOAA GHCN-Daily: external, non-NASA reference; Alexandria mean-temperature coverage ends 2023-08-09.
- No MOD13Q1 NDVI or MOD11A2 LST files were supplied. These indicators remain unavailable.
- One year supports seasonal description only, not long-term trend or forecast inference.

The detailed setup steps, Windows double-click launchers, and Render Blueprint instructions are in the root `README.md` and `docs/DEPLOYMENT_GUIDE_AR.md`.
