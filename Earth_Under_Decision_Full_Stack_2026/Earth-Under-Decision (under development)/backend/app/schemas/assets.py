from datetime import datetime
from pydantic import BaseModel, ConfigDict


class DataAssetRead(BaseModel):
    id: str
    dataset_id: str | None
    source_id: str | None
    original_filename: str
    detected_format: str
    content_type: str | None
    size_bytes: int
    sha256: str
    status: str
    validation_status: str
    detected_metadata: dict
    operator_metadata: dict
    warnings: list
    errors: list
    is_raw: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class UploadResult(BaseModel):
    asset: DataAssetRead
    duplicate: bool = False
    scientific_validation: str = "pending"
    note: str
