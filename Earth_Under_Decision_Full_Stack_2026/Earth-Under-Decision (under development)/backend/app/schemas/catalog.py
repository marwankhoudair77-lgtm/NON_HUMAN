from pydantic import BaseModel, ConfigDict


class IndicatorRead(BaseModel):
    id: str
    name: str
    name_ar: str
    description: str
    units: str
    data_status: str
    candidate_product_id: str
    observation_modes: list[str] | None = None
    release_status: str | None = None


class DataSourceRead(BaseModel):
    id: str
    key: str
    name: str
    provider: str
    official_url: str | None
    access_method: str
    connector_status: str
    metadata_verified: bool
    notes: str | None = None
    model_config = ConfigDict(from_attributes=True)


class DatasetRead(BaseModel):
    id: str
    source_id: str | None
    product_id: str
    version: str | None
    name: str
    indicator: str
    platform: str | None
    spatial_resolution_m: float | None
    temporal_resolution: str | None
    units: str | None
    verification_status: str
    metadata_json: dict
    model_config = ConfigDict(from_attributes=True)


class StudyAreaRead(BaseModel):
    id: str
    parent_id: str | None
    name: str
    name_ar: str | None
    area_type: str
    boundary_source: str | None
    boundary_version: str | None
    crs: str | None
    validation_status: str
    geometry_geojson: dict | None
    notes: str | None
    model_config = ConfigDict(from_attributes=True)
