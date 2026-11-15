from functools import lru_cache
from pathlib import Path
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="../.env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_env: str = "development"
    app_name: str = "Earth Under Decision"
    api_v1_prefix: str = "/api/v1"
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    database_url: str = "postgresql+psycopg://earth_app:CHANGE_ME_LOCAL_PASSWORD@localhost:5432/earth_under_decision"
    storage_backend: str = "local"
    local_storage_root: Path = Path("../data")
    max_upload_size_mb: int = Field(default=500, ge=1, le=10000)
    admin_api_token: str | None = None
    cors_origins: str = "http://localhost:5173"
    nasa_earthdata_username: str | None = None
    nasa_earthdata_password: str | None = None
    nasa_earthdata_token: str | None = None
    s3_endpoint_url: str | None = None
    s3_bucket: str | None = None
    s3_region: str | None = None
    s3_access_key_id: str | None = None
    s3_secret_access_key: str | None = None

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_postgres_driver(cls, value):
        # Render provides postgresql:// connection strings. This project uses psycopg v3.
        if isinstance(value, str):
            if value.startswith("postgres://"):
                return value.replace("postgres://", "postgresql+psycopg://", 1)
            if value.startswith("postgresql://"):
                return value.replace("postgresql://", "postgresql+psycopg://", 1)
        return value

    @property
    def cors_origin_list(self) -> list[str]:
        return [part.strip() for part in self.cors_origins.split(",") if part.strip()]

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
