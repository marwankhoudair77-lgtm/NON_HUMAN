import hashlib
from pathlib import Path
from fastapi import UploadFile, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.geospatial.inspect import detect_format, inspect_file, UnsupportedRasterFormat
from app.models import DataAsset, Dataset
from app.storage.factory import get_storage

ALLOWED_EXTENSIONS = {".tif", ".tiff", ".hdf", ".h4", ".h5", ".nc", ".nc4"}
CHUNK_SIZE = 1024 * 1024


async def save_uploaded_asset(
    db: Session,
    upload: UploadFile,
    dataset_id: str | None,
    source_id: str | None,
    operator_metadata: dict,
) -> DataAsset:
    settings = get_settings()
    original_filename = Path((upload.filename or "unnamed").replace("\\", "/")).name[:255]
    extension = Path(original_filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(415, detail={"code": "unsupported_extension", "message": "Allowed extensions: GeoTIFF, HDF/HDF5, and NetCDF."})

    if dataset_id:
        dataset = db.get(Dataset, dataset_id)
        if dataset is None:
            raise HTTPException(404, detail={"code": "dataset_not_found", "message": "The selected dataset does not exist in the catalog."})
        if source_id is None:
            source_id = dataset.source_id
    if source_id:
        from app.models import DataSource
        if db.get(DataSource, source_id) is None:
            raise HTTPException(404, detail={"code": "source_not_found", "message": "The selected data source does not exist in the catalog."})

    storage = get_storage()
    temp_path, _ = storage.create_raw_temp_file()
    sha256 = hashlib.sha256()
    size = 0
    try:
        with temp_path.open("wb") as output:
            while chunk := await upload.read(CHUNK_SIZE):
                size += len(chunk)
                if size > settings.max_upload_bytes:
                    raise HTTPException(413, detail={"code": "upload_too_large", "message": f"Maximum upload size is {settings.max_upload_size_mb} MB."})
                sha256.update(chunk)
                output.write(chunk)
        if size == 0:
            raise HTTPException(400, detail={"code": "empty_file", "message": "The uploaded file is empty."})
        checksum = sha256.hexdigest()
        duplicate_query = select(DataAsset).where(DataAsset.sha256 == checksum, DataAsset.dataset_id == dataset_id)
        duplicate = db.scalar(duplicate_query)
        if duplicate:
            raise HTTPException(409, detail={"code": "duplicate_asset", "asset_id": duplicate.id, "message": "A file with the same checksum and dataset identity is already registered."})
        try:
            detected_format = detect_format(temp_path, original_filename)
        except UnsupportedRasterFormat as exc:
            raise HTTPException(415, detail={"code": "unsupported_file_signature", "message": str(exc)}) from exc
        expected_formats = {
            ".tif": {"GeoTIFF"}, ".tiff": {"GeoTIFF"},
            ".nc": {"NetCDF", "NetCDF4"}, ".nc4": {"NetCDF4"},
            ".hdf": {"HDF4", "HDF5", "NetCDF4"}, ".h4": {"HDF4"}, ".h5": {"HDF5", "NetCDF4"},
        }
        if detected_format not in expected_formats.get(extension, set()):
            raise HTTPException(415, detail={"code": "extension_signature_mismatch", "message": "File extension does not match the detected file signature."})
        try:
            detected_metadata, warnings = inspect_file(temp_path, detected_format)
            metadata_inspection = "completed"
        except Exception as exc:
            detected_metadata = {"format": detected_format, "metadata_inspection": "failed", "error_type": type(exc).__name__}
            warnings = ["The file signature was recognized, but full metadata inspection failed. Manual review is required."]
            metadata_inspection = "incomplete"

        storage_key = storage.commit_raw(temp_path, extension)
        asset = DataAsset(
            dataset_id=dataset_id,
            source_id=source_id,
            original_filename=original_filename,
            storage_key=storage_key,
            detected_format=detected_format,
            content_type=upload.content_type,
            size_bytes=size,
            sha256=checksum,
            status="uploaded_pending_review",
            validation_status="pending_scientific_validation",
            detected_metadata={**detected_metadata, "metadata_inspection": metadata_inspection},
            operator_metadata=operator_metadata,
            warnings=warnings,
            errors=[],
            is_raw=True,
        )
        db.add(asset)
        try:
            db.commit()
            db.refresh(asset)
            return asset
        except Exception:
            db.rollback()
            stored_path = storage.resolve(storage_key)
            try:
                stored_path.chmod(0o600)
                stored_path.unlink(missing_ok=True)
            except OSError:
                pass
            raise
    except Exception:
        storage.delete_temp(temp_path)
        raise
