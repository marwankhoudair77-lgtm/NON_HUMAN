from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import DataAsset, Dataset, RasterLayer, StudyArea

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard/summary")
def dashboard_summary(db: Session = Depends(get_db)):
    dataset_count = db.scalar(select(func.count()).select_from(Dataset)) or 0
    raw_asset_count = db.scalar(select(func.count()).select_from(DataAsset).where(DataAsset.is_raw.is_(True))) or 0
    verified_asset_count = db.scalar(select(func.count()).select_from(DataAsset).where(DataAsset.validation_status == "scientifically_validated")) or 0
    available_layer_count = db.scalar(select(func.count()).select_from(RasterLayer).where(RasterLayer.status == "available")) or 0
    validated_area_count = db.scalar(select(func.count()).select_from(StudyArea).where(StudyArea.validation_status == "validated")) or 0
    return {
        "data_status": "available" if verified_asset_count > 0 else "unavailable",
        "dataset_catalog_count": dataset_count,
        "raw_asset_count": raw_asset_count,
        "scientifically_validated_asset_count": verified_asset_count,
        "available_map_layer_count": available_layer_count,
        "validated_study_area_count": validated_area_count,
        "scientific_metrics": None,
        "message": "No scientifically validated observation assets are connected yet." if verified_asset_count == 0 else None,
    }
