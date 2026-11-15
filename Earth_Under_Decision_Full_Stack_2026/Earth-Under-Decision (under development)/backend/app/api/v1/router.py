from fastapi import APIRouter
from app.api.v1.endpoints import analysis, assets, catalog, dashboard, health, jobs, maps, scenarios, storytelling

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(catalog.router, prefix="/api/v1")
api_router.include_router(assets.router, prefix="/api/v1")
api_router.include_router(jobs.router, prefix="/api/v1")
api_router.include_router(dashboard.router, prefix="/api/v1")
api_router.include_router(analysis.router, prefix="/api/v1")
api_router.include_router(maps.router, prefix="/api/v1")
api_router.include_router(scenarios.router, prefix="/api/v1")
api_router.include_router(storytelling.router, prefix="/api/v1")
