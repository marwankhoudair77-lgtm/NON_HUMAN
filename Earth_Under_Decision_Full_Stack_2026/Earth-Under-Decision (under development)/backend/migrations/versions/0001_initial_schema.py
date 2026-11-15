"""Initial Earth Under Decision schema.

Revision ID: 0001_initial
Revises:
Create Date: 2026-11-14
"""
from alembic import op
from app.db.base import Base
import app.models  # noqa: F401

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    # Initial revision creates the frozen model metadata for every table in this baseline.
    # Future revisions should use explicit Alembic operations and must never rewrite this file.
    Base.metadata.create_all(bind=bind)

    bind.exec_driver_sql("""
        INSERT INTO data_sources
        (id, key, name, provider, official_url, access_method, connector_status, metadata_verified, notes, created_at, updated_at)
        VALUES
        ('source-appeears', 'nasa_appeears', 'NASA LP DAAC AppEEARS', 'NASA / USGS LP DAAC', 'https://appeears.earthdatacloud.nasa.gov/', 'official_api_or_manual_upload', 'pending_connector_verification', FALSE, 'Candidate source adapter. No download connector is claimed as active.', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        ('source-gesdisc', 'nasa_gesdisc', 'NASA GES DISC / Earthdata', 'NASA', 'https://disc.gsfc.nasa.gov/', 'official_earthdata_service_or_manual_upload', 'pending_connector_verification', FALSE, 'Candidate source adapter for GPM; release and access workflow require verification.', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ON CONFLICT (key) DO NOTHING
    """)
    bind.exec_driver_sql("""
        INSERT INTO datasets
        (id, source_id, product_id, version, name, indicator, platform, spatial_resolution_m, temporal_resolution, units, verification_status, metadata_json, created_at, updated_at)
        VALUES
        ('dataset-mod13q1', 'source-appeears', 'MOD13Q1', '061', 'MODIS Terra Vegetation Indices 16-Day', 'ndvi', 'Terra MODIS', 250, '16-day composite', 'dimensionless', 'candidate_metadata_not_file_verified', '{"candidate":true,"downloaded":false,"validated":false}', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        ('dataset-mod11a2', 'source-appeears', 'MOD11A2', '061', 'MODIS Terra Land Surface Temperature 8-Day', 'lst', 'Terra MODIS', 1000, '8-day composite', 'must_be_confirmed_from_product_metadata', 'candidate_metadata_not_file_verified', '{"candidate":true,"downloaded":false,"validated":false,"day_night_separate":true}', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        ('dataset-gpm-imerg', 'source-gesdisc', 'GPM_3IMERGDF_07', 'pending_release_verification', 'GPM IMERG Final Daily', 'precipitation', 'GPM IMERG', NULL, 'daily; verify exact release', 'must_be_confirmed_from_product_metadata', 'release_pending_verification', '{"candidate":true,"downloaded":false,"validated":false,"release_metadata_verified":false}', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ON CONFLICT (id) DO NOTHING
    """)
    bind.exec_driver_sql("""
        INSERT INTO study_areas
        (id, parent_id, name, name_ar, area_type, boundary_source, boundary_version, crs, validation_status, geometry, geometry_geojson, notes, created_at, updated_at)
        VALUES
        ('area-global', NULL, 'Global Context', 'السياق العالمي', 'global', NULL, NULL, NULL, 'reference_only_no_geometry', NULL, NULL, 'Context entry only; no geometry supplied.', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        ('area-egypt', 'area-global', 'Egypt', 'مصر', 'country', NULL, NULL, NULL, 'boundary_pending_validation', NULL, NULL, 'Country boundary must be sourced and validated before spatial calculations.', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        ('area-nile-delta', 'area-egypt', 'Nile Delta Pilot', 'دلتا النيل', 'pilot_region', NULL, NULL, NULL, 'candidate_unvalidated', NULL, NULL, 'Preliminary pilot area; no authoritative geometry is included.', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        ('area-gharbia', 'area-nile-delta', 'Gharbia', 'الغربية', 'governorate', NULL, NULL, NULL, 'candidate_unvalidated', NULL, NULL, 'Candidate governorate; boundary not loaded or verified.', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        ('area-kafr-el-sheikh', 'area-nile-delta', 'Kafr El-Sheikh', 'كفر الشيخ', 'governorate', NULL, NULL, NULL, 'candidate_unvalidated', NULL, NULL, 'Candidate governorate; boundary not loaded or verified.', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        ('area-sharqia', 'area-nile-delta', 'Sharqia', 'الشرقية', 'governorate', NULL, NULL, NULL, 'candidate_unvalidated', NULL, NULL, 'Candidate governorate; boundary not loaded or verified.', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ON CONFLICT (id) DO NOTHING
    """)


def downgrade() -> None:
    # Dropping the schema destroys registered metadata. Explicit operator action is required.
    # This project deliberately prevents an accidental destructive downgrade.
    raise RuntimeError("Destructive downgrade is disabled. Back up the database and review tables manually.")
