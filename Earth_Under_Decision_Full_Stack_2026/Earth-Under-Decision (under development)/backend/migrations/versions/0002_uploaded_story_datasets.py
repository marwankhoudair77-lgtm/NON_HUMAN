"""Register the actual uploaded 2023 GLDAS/GPM exports and NOAA reference.

Revision ID: 0002_story_data
Revises: 0001_initial
"""
from alembic import op

revision = "0002_story_data"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    bind.exec_driver_sql("""
        UPDATE datasets
        SET product_id='GPM_3IMERGM',
            version='07',
            name='GPM IMERG Monthly Final Run — 2023 time-averaged precipitation rate',
            temporal_resolution='monthly product; time mean over 2023; 0.1 degree grid',
            units='mm/hr time-mean; annualized equivalent derived',
            verification_status='source_file_metadata_inspected_scientific_review_pending',
            metadata_json='{"uploaded":true,"source_file_metadata_inspected":true,"product_short_name":"GPM_3IMERGM","version":"07","units":"mm/hr","cell_methods":"time: mean","period":"2023-01-01/2024-01-01","spatial_resolution":"0.1 degree","annualized_equivalent_is_derived":true,"scientific_validation":false}'
        WHERE id='dataset-gpm-imerg'
    """)
    bind.exec_driver_sql("""
        INSERT INTO data_sources
        (id, key, name, provider, official_url, access_method, connector_status, metadata_verified, notes, created_at, updated_at)
        VALUES
        ('source-gldas', 'nasa_gldas_gesdisc', 'NASA GLDAS / GES DISC', 'NASA Goddard Earth Sciences Data and Information Services Center', 'https://disc.gsfc.nasa.gov/datasets/GLDAS_NOAH025_3H_2.1/summary', 'uploaded_source_export; official_download_connector_pending', 'uploaded_data_present_connector_pending', TRUE, 'Uploaded source exports identify GLDAS_NOAH025_3H 2.1 variables Evap_tavg and RootMoist_inst. Product definitions and units are supported by GES DISC metadata; per-pixel QA and scientific validation are still pending.', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        ('source-noaa-ghcn', 'noaa_ghcn_daily', 'NOAA GHCN-Daily', 'NOAA National Centers for Environmental Information', 'https://www.ncei.noaa.gov/products/land-based-station/global-historical-climatology-network-daily', 'operator_provided_csv_export', 'external_reference_only', FALSE, 'External comparison dataset, not NASA. Alexandria station coverage in the supplied file ends 2023-08-09; missing observations remain null.', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ON CONFLICT (id) DO NOTHING
    """)
    bind.exec_driver_sql("""
        INSERT INTO datasets
        (id, source_id, product_id, version, name, indicator, platform, spatial_resolution_m, temporal_resolution, units, verification_status, metadata_json, created_at, updated_at)
        VALUES
        ('dataset-gldas-et', 'source-gldas', 'GLDAS_NOAH025_3H', '2.1', 'GLDAS Noah 3-hourly Evapotranspiration — point export 2023', 'evapotranspiration', 'GLDAS Noah', 25000, '3-hourly source; daily aggregation derived for 2023', 'kg m-2 s-1 source; mm/day derived', 'uploaded_and_processed_scientific_review_pending', '{"uploaded":true,"variable":"Evap_tavg","point":{"lat":30.9,"lon":31.0},"source_frequency":"3-hourly","daily_rows":365,"qa_applied":false,"area_average":false}', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        ('dataset-gldas-root', 'source-gldas', 'GLDAS_NOAH025_3H', '2.1', 'GLDAS Noah Root-zone Soil Moisture — point export 2023', 'root_moisture', 'GLDAS Noah', 25000, '3-hourly source; daily mean/min/max derived for 2023', 'kg m-2', 'uploaded_and_processed_scientific_review_pending', '{"uploaded":true,"variable":"RootMoist_inst","point":{"lat":30.9,"lon":31.0},"source_frequency":"3-hourly","daily_rows":365,"qa_applied":false,"area_average":false}', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        ('dataset-noaa-alex', 'source-noaa-ghcn', 'GHCN-Daily', NULL, 'NOAA Alexandria station daily observations — comparison only', 'air_temperature_reference', 'NOAA station', NULL, 'daily; incomplete coverage 2023-01-01 to 2023-08-09', '°C', 'external_reference_incomplete_not_nasa', '{"uploaded":true,"station":"ALEXANDRIA INTERNATIONAL, EG","not_nasa":true,"valid_mean_temperature_days":219,"analysis_role":"external_comparison_only"}', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ON CONFLICT (id) DO NOTHING
    """)


def downgrade() -> None:
    # Preserve uploaded catalog data; downgrade does not delete source records.
    bind = op.get_bind()
    bind.exec_driver_sql("""
        UPDATE datasets
        SET product_id='GPM_3IMERGDF_07', version='pending_release_verification',
            name='GPM IMERG Final Daily', temporal_resolution='daily; verify exact release',
            units='must_be_confirmed_from_product_metadata', verification_status='release_pending_verification',
            metadata_json='{"candidate":true,"downloaded":false,"validated":false,"release_metadata_verified":false}'
        WHERE id='dataset-gpm-imerg'
    """)
