from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from app.db.types import PostGISMultiPolygon


def new_id() -> str:
    return str(uuid4())


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class DataSource(TimestampMixin, Base):
    __tablename__ = "data_sources"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    key: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    provider: Mapped[str] = mapped_column(String(120), nullable=False)
    official_url: Mapped[str | None] = mapped_column(Text)
    access_method: Mapped[str] = mapped_column(String(80), default="manual_or_official_api", nullable=False)
    connector_status: Mapped[str] = mapped_column(String(60), default="pending_verification", nullable=False)
    metadata_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)


class Dataset(TimestampMixin, Base):
    __tablename__ = "datasets"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    source_id: Mapped[str | None] = mapped_column(ForeignKey("data_sources.id", ondelete="SET NULL"), index=True)
    product_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    version: Mapped[str | None] = mapped_column(String(60))
    name: Mapped[str] = mapped_column(String(240), nullable=False)
    indicator: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    platform: Mapped[str | None] = mapped_column(String(100))
    spatial_resolution_m: Mapped[float | None] = mapped_column(Float)
    temporal_resolution: Mapped[str | None] = mapped_column(String(100))
    units: Mapped[str | None] = mapped_column(String(100))
    verification_status: Mapped[str] = mapped_column(String(60), default="candidate", nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)


class DataAsset(TimestampMixin, Base):
    __tablename__ = "data_assets"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    dataset_id: Mapped[str | None] = mapped_column(ForeignKey("datasets.id", ondelete="SET NULL"), index=True)
    source_id: Mapped[str | None] = mapped_column(ForeignKey("data_sources.id", ondelete="SET NULL"), index=True)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    detected_format: Mapped[str] = mapped_column(String(40), nullable=False)
    content_type: Mapped[str | None] = mapped_column(String(150))
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(60), default="uploaded", nullable=False, index=True)
    validation_status: Mapped[str] = mapped_column(String(60), default="pending_scientific_validation", nullable=False)
    detected_metadata: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    operator_metadata: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    warnings: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    errors: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    is_raw: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    __table_args__ = (
        Index("ix_data_assets_checksum_dataset", "sha256", "dataset_id"),
    )


class StudyArea(TimestampMixin, Base):
    __tablename__ = "study_areas"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    parent_id: Mapped[str | None] = mapped_column(ForeignKey("study_areas.id", ondelete="SET NULL"), index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    name_ar: Mapped[str | None] = mapped_column(String(200))
    area_type: Mapped[str] = mapped_column(String(60), nullable=False)
    boundary_source: Mapped[str | None] = mapped_column(Text)
    boundary_version: Mapped[str | None] = mapped_column(String(100))
    crs: Mapped[str | None] = mapped_column(String(40))
    validation_status: Mapped[str] = mapped_column(String(60), default="candidate_unvalidated", nullable=False)
    geometry: Mapped[str | None] = mapped_column(PostGISMultiPolygon())
    geometry_geojson: Mapped[dict | None] = mapped_column(JSON)
    notes: Mapped[str | None] = mapped_column(Text)
    __table_args__ = (Index("ix_study_areas_geometry", "geometry", postgresql_using="gist"),)


class ProcessingJob(TimestampMixin, Base):
    __tablename__ = "processing_jobs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    asset_id: Mapped[str | None] = mapped_column(ForeignKey("data_assets.id", ondelete="SET NULL"), index=True)
    job_type: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="queued", nullable=False, index=True)
    progress_percent: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    message: Mapped[str | None] = mapped_column(Text)
    error_code: Mapped[str | None] = mapped_column(String(80))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ProcessingRun(TimestampMixin, Base):
    __tablename__ = "processing_runs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    job_id: Mapped[str | None] = mapped_column(ForeignKey("processing_jobs.id", ondelete="SET NULL"), index=True)
    source_asset_id: Mapped[str] = mapped_column(ForeignKey("data_assets.id"), nullable=False)
    output_asset_id: Mapped[str | None] = mapped_column(ForeignKey("data_assets.id", ondelete="SET NULL"))
    operation: Mapped[str] = mapped_column(String(100), nullable=False)
    parameters: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    software_version: Mapped[str | None] = mapped_column(String(100))
    provenance: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    warnings: Mapped[list] = mapped_column(JSON, default=list, nullable=False)


class RasterLayer(TimestampMixin, Base):
    __tablename__ = "raster_layers"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    asset_id: Mapped[str] = mapped_column(ForeignKey("data_assets.id", ondelete="CASCADE"), nullable=False, index=True)
    indicator: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    variable: Mapped[str] = mapped_column(String(120), nullable=False)
    observation_mode: Mapped[str | None] = mapped_column(String(30))
    units: Mapped[str | None] = mapped_column(String(100))
    interval_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    interval_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source_product_id: Mapped[str | None] = mapped_column(String(100))
    source_version: Mapped[str | None] = mapped_column(String(60))
    crs: Mapped[str | None] = mapped_column(String(40))
    native_resolution_m: Mapped[float | None] = mapped_column(Float)
    visualization_range: Mapped[dict | None] = mapped_column(JSON)
    palette: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(40), default="unavailable", nullable=False)
    tile_service_url: Mapped[str | None] = mapped_column(Text)
    provenance: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)


class AnalysisRun(TimestampMixin, Base):
    __tablename__ = "analysis_runs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    indicator: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    study_area_id: Mapped[str | None] = mapped_column(ForeignKey("study_areas.id", ondelete="SET NULL"), index=True)
    method: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="pending", nullable=False)
    parameters: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    provenance: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    warnings: Mapped[list] = mapped_column(JSON, default=list, nullable=False)


class AnalysisResult(TimestampMixin, Base):
    __tablename__ = "analysis_results"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    analysis_run_id: Mapped[str] = mapped_column(ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    result_type: Mapped[str] = mapped_column(String(80), nullable=False)
    value: Mapped[float | None] = mapped_column(Float)
    unit: Mapped[str | None] = mapped_column(String(100))
    p_value: Mapped[float | None] = mapped_column(Float)
    confidence_interval: Mapped[dict | None] = mapped_column(JSON)
    sample_size: Mapped[int | None] = mapped_column(Integer)
    details: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)


class TimeSeriesValue(Base):
    __tablename__ = "time_series_values"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    analysis_run_id: Mapped[str] = mapped_column(ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    study_area_id: Mapped[str | None] = mapped_column(ForeignKey("study_areas.id", ondelete="SET NULL"), index=True)
    indicator: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    interval_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    interval_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    value: Mapped[float | None] = mapped_column(Float)
    units: Mapped[str | None] = mapped_column(String(100))
    valid_pixel_count: Mapped[int | None] = mapped_column(Integer)
    missing_pixel_count: Mapped[int | None] = mapped_column(Integer)
    quality_summary: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)


class Scenario(TimestampMixin, Base):
    __tablename__ = "scenarios"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    indicator: Mapped[str] = mapped_column(String(40), nullable=False)
    study_area_id: Mapped[str | None] = mapped_column(ForeignKey("study_areas.id", ondelete="SET NULL"), index=True)
    assumptions: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    baseline_reference: Mapped[str | None] = mapped_column(String(200))
    calculation_method: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(60), default="illustrative_only", nullable=False)
    result: Mapped[dict | None] = mapped_column(JSON)
