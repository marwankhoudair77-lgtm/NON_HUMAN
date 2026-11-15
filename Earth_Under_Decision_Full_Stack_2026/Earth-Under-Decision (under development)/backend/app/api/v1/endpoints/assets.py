from fastapi import APIRouter, Depends, File, Form, UploadFile, Query, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.security import require_admin_token
from app.db.session import get_db
from app.models import DataAsset
from app.services.assets import save_uploaded_asset
from app.schemas.assets import DataAssetRead

router = APIRouter(tags=["data-assets"])


@router.post("/data-assets/upload", dependencies=[Depends(require_admin_token)])
async def upload_data_asset(
    file: UploadFile = File(...),
    dataset_id: str | None = Form(default=None),
    source_id: str | None = Form(default=None),
    operator_notes: str | None = Form(default=None, max_length=2000),
    db: Session = Depends(get_db),
):
    asset = await save_uploaded_asset(
        db=db,
        upload=file,
        dataset_id=dataset_id,
        source_id=source_id,
        operator_metadata={"notes": operator_notes} if operator_notes else {},
    )
    return {
        "asset": DataAssetRead.model_validate(asset),
        "duplicate": False,
        "scientific_validation": "pending",
        "note": "Original file stored in the raw area. Format/metadata inspection is not scientific validation; product-specific QA and provenance review are still required.",
    }


@router.get("/data-assets")
def list_assets(
    dataset_id: str | None = None,
    status: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    query = select(DataAsset)
    if dataset_id:
        query = query.where(DataAsset.dataset_id == dataset_id)
    if status:
        query = query.where(DataAsset.status == status)
    rows = db.scalars(query.order_by(DataAsset.created_at.desc()).limit(limit).offset(offset)).all()
    return {"items": [DataAssetRead.model_validate(row) for row in rows], "count": len(rows), "limit": limit, "offset": offset}


@router.get("/data-assets/{asset_id}")
def get_asset(asset_id: str, db: Session = Depends(get_db)):
    row = db.get(DataAsset, asset_id)
    if row is None:
        raise HTTPException(404, detail={"code": "asset_not_found", "message": "Data asset not found."})
    return DataAssetRead.model_validate(row)
