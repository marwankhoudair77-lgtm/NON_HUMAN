from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import DataAsset, RasterLayer

router = APIRouter(tags=["maps"])


@router.get("/maps/layers")
def list_map_layers(indicator: str | None = None, observation_mode: str | None = None, db: Session = Depends(get_db)):
    query = select(RasterLayer).join(DataAsset, RasterLayer.asset_id == DataAsset.id).where(
        RasterLayer.status == "available",
        DataAsset.validation_status == "scientifically_validated",
    )
    if indicator:
        query = query.where(RasterLayer.indicator == indicator)
    if observation_mode:
        query = query.where(RasterLayer.observation_mode == observation_mode)
    rows = db.scalars(query.order_by(RasterLayer.created_at.desc())).all()
    return {
        "items": [
            {
                "id": row.id,
                "indicator": row.indicator,
                "variable": row.variable,
                "observation_mode": row.observation_mode,
                "units": row.units,
                "interval_start": row.interval_start.isoformat() if row.interval_start else None,
                "interval_end": row.interval_end.isoformat() if row.interval_end else None,
                "source_product_id": row.source_product_id,
                "source_version": row.source_version,
                "crs": row.crs,
                "native_resolution_m": row.native_resolution_m,
                "visualization_range": row.visualization_range,
                "palette": row.palette,
                "status": row.status,
                "tile_service_url": row.tile_service_url,
                "provenance": row.provenance,
            }
            for row in rows
        ],
        "count": len(rows),
        "data_status": "available" if rows else "unavailable",
        "message": None if rows else "No map layer is served because no scientifically validated processed raster is registered.",
    }


@router.get("/maps/layers/{layer_id}")
def get_map_layer(layer_id: str, db: Session = Depends(get_db)):
    row = db.get(RasterLayer, layer_id)
    if row is None or row.status != "available":
        raise HTTPException(404, detail={"code": "map_layer_unavailable", "message": "The requested map layer is not available."})
    asset = db.get(DataAsset, row.asset_id)
    if asset is None or asset.validation_status != "scientifically_validated":
        raise HTTPException(404, detail={"code": "map_layer_unavailable", "message": "The requested map layer has no scientifically validated source asset."})
    return {
        "id": row.id,
        "indicator": row.indicator,
        "variable": row.variable,
        "observation_mode": row.observation_mode,
        "units": row.units,
        "interval_start": row.interval_start.isoformat() if row.interval_start else None,
        "interval_end": row.interval_end.isoformat() if row.interval_end else None,
        "source_product_id": row.source_product_id,
        "source_version": row.source_version,
        "crs": row.crs,
        "native_resolution_m": row.native_resolution_m,
        "visualization_range": row.visualization_range,
        "palette": row.palette,
        "tile_service_url": row.tile_service_url,
        "provenance": row.provenance,
    }
