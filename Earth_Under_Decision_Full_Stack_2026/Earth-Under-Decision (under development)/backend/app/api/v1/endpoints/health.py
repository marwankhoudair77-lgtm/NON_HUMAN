from fastapi import APIRouter, Response
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from app.core.config import get_settings
from app.db.session import engine

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    settings = get_settings()
    return {"status": "ok", "service": settings.app_name, "environment": settings.app_env}


@router.get("/ready")
def ready(response: Response):
    checks = {"database": False, "postgis": False}
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            checks["database"] = True
            try:
                connection.execute(text("SELECT PostGIS_Full_Version()"))
                checks["postgis"] = True
            except SQLAlchemyError:
                checks["postgis"] = False
    except SQLAlchemyError:
        pass
    is_ready = all(checks.values())
    response.status_code = 200 if is_ready else 503
    return {"status": "ready" if is_ready else "not_ready", "checks": checks}
