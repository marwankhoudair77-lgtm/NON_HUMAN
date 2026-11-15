from fastapi import APIRouter, Query
from app.services.story_data import build_summary, catalog, daily_series, monthly_series, precipitation_geojson

router = APIRouter(prefix="/storytelling", tags=["storytelling-data"])


@router.get("/summary")
def get_story_summary():
    return build_summary()


@router.get("/monthly")
def get_monthly_story_series():
    return monthly_series()


@router.get("/daily")
def get_daily_story_series(
    variable: str = Query(pattern="^(evapotranspiration|root_moisture|noaa_air_temperature)$"),
    start: str | None = None,
    end: str | None = None,
):
    return daily_series(variable=variable, start=start, end=end)


@router.get("/precipitation-grid")
def get_precipitation_grid():
    return precipitation_geojson()


@router.get("/catalog")
def get_story_catalog():
    return catalog()
