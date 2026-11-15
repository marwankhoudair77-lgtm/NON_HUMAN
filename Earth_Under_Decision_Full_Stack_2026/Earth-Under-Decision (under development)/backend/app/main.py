import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging()
    application = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description=(
            "Earth observation and environmental decision-support API. "
            "Only explicitly validated assets and analysis results are presented as scientific outputs."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )
    application.include_router(api_router)

    # In the bundled deployment, FastAPI serves the compiled Vite application
    # from the same origin. During Vite development this directory is absent,
    # so the frontend runs on port 5173 and proxies /api and /health to the API.
    static_dir = Path(os.getenv("FRONTEND_DIST_DIR", "/app/frontend_dist")).resolve()
    if static_dir.is_dir() and (static_dir / "index.html").is_file():
        assets_dir = static_dir / "assets"
        if assets_dir.is_dir():
            application.mount("/assets", StaticFiles(directory=assets_dir), name="frontend-assets")

        @application.get("/{requested_path:path}", include_in_schema=False)
        async def serve_frontend(requested_path: str):
            if requested_path.startswith(("api/", "docs", "redoc", "openapi.json", "health", "ready")):
                raise HTTPException(status_code=404, detail="Not found")
            candidate = (static_dir / requested_path).resolve()
            if candidate.is_relative_to(static_dir) and candidate.is_file():
                return FileResponse(candidate)
            return FileResponse(static_dir / "index.html")

    return application


app = create_app()
