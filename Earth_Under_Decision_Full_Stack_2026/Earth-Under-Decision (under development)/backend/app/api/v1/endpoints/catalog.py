from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import DataSource, Dataset, StudyArea
from app.models.constants import INDICATORS

router = APIRouter(tags=["catalog"])


@router.get("/indicators")
def list_indicators():
    return {"items": INDICATORS, "count": len(INDICATORS)}


@router.get("/data-sources")
def list_data_sources(db: Session = Depends(get_db)):
    rows = db.scalars(select(DataSource).order_by(DataSource.name)).all()
    return {"items": [
        {"id": row.id, "key": row.key, "name": row.name, "provider": row.provider,
         "official_url": row.official_url, "access_method": row.access_method,
         "connector_status": row.connector_status, "metadata_verified": row.metadata_verified,
         "notes": row.notes}
        for row in rows
    ], "count": len(rows)}


@router.get("/datasets")
def list_datasets(
    indicator: str | None = Query(default=None, pattern="^(ndvi|lst|precipitation|evapotranspiration|root_moisture|air_temperature_reference)$"),
    verification_status: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    query = select(Dataset)
    if indicator:
        query = query.where(Dataset.indicator == indicator)
    if verification_status:
        query = query.where(Dataset.verification_status == verification_status)
    rows = db.scalars(query.order_by(Dataset.product_id).limit(limit).offset(offset)).all()
    return {"items": [
        {"id": row.id, "source_id": row.source_id, "product_id": row.product_id, "version": row.version,
         "name": row.name, "indicator": row.indicator, "platform": row.platform,
         "spatial_resolution_m": row.spatial_resolution_m, "temporal_resolution": row.temporal_resolution,
         "units": row.units, "verification_status": row.verification_status, "metadata_json": row.metadata_json}
        for row in rows
    ], "count": len(rows), "limit": limit, "offset": offset}


@router.get("/datasets/{dataset_id}")
def get_dataset(dataset_id: str, db: Session = Depends(get_db)):
    row = db.get(Dataset, dataset_id)
    if row is None:
        from fastapi import HTTPException
        raise HTTPException(404, detail={"code": "dataset_not_found", "message": "Dataset not found."})
    return {"id": row.id, "source_id": row.source_id, "product_id": row.product_id, "version": row.version,
            "name": row.name, "indicator": row.indicator, "platform": row.platform,
            "spatial_resolution_m": row.spatial_resolution_m, "temporal_resolution": row.temporal_resolution,
            "units": row.units, "verification_status": row.verification_status, "metadata_json": row.metadata_json}


@router.get("/study-areas")
def list_study_areas(
    validation_status: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    query = select(StudyArea)
    if validation_status:
        query = query.where(StudyArea.validation_status == validation_status)
    rows = db.scalars(query.order_by(StudyArea.name).limit(limit).offset(offset)).all()
    return {"items": [
        {"id": row.id, "parent_id": row.parent_id, "name": row.name, "name_ar": row.name_ar,
         "area_type": row.area_type, "boundary_source": row.boundary_source,
         "boundary_version": row.boundary_version, "crs": row.crs,
         "validation_status": row.validation_status, "geometry_geojson": row.geometry_geojson, "notes": row.notes}
        for row in rows
    ], "count": len(rows), "limit": limit, "offset": offset}


@router.get("/study-areas/{area_id}")
def get_study_area(area_id: str, db: Session = Depends(get_db)):
    row = db.get(StudyArea, area_id)
    if row is None:
        from fastapi import HTTPException
        raise HTTPException(404, detail={"code": "study_area_not_found", "message": "Study area not found."})
    return {"id": row.id, "parent_id": row.parent_id, "name": row.name, "name_ar": row.name_ar,
            "area_type": row.area_type, "boundary_source": row.boundary_source,
            "boundary_version": row.boundary_version, "crs": row.crs,
            "validation_status": row.validation_status, "geometry_geojson": row.geometry_geojson, "notes": row.notes}
