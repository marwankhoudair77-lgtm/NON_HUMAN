from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.main import app
from app.db.base import Base
from app.db.session import get_db




def make_test_db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    def override_get_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()
    app.dependency_overrides[get_db] = override_get_db
    return engine


def test_health_and_indicators():
    engine = make_test_db()
    client = TestClient(app)
    assert client.get("/health").json()["status"] == "ok"
    data = client.get("/api/v1/indicators").json()
    assert {item["id"] for item in data["items"]} == {"ndvi", "lst", "precipitation", "evapotranspiration", "root_moisture", "air_temperature_reference"}
    assert client.get("/api/v1/dashboard/summary").json()["data_status"] == "unavailable"
    client.close()
    app.dependency_overrides.clear()
    engine.dispose()


def test_upload_requires_admin_token():
    engine = make_test_db()
    client = TestClient(app)
    response = client.post("/api/v1/data-assets/upload", files={"file": ("wrong.tif", b"fake", "image/tiff")})
    assert response.status_code == 401
    client.close()
    app.dependency_overrides.clear()
    engine.dispose()


def test_upload_keeps_file_unverified_and_returns_metadata(tmp_path, monkeypatch):
    import numpy as np
    import rasterio
    from rasterio.io import MemoryFile
    from app.storage.local import LocalStorage
    import app.services.assets as asset_service

    engine = make_test_db()
    monkeypatch.setattr(asset_service, "get_storage", lambda: LocalStorage(tmp_path / "storage"))
    # The upload flow writes only a raw original and labels science validation as pending.
    mem = MemoryFile()
    with mem.open(driver="GTiff", width=2, height=2, count=1, dtype="uint8", crs="EPSG:4326", transform=rasterio.transform.from_origin(30, 31, 0.01, 0.01)) as dst:
        dst.write(np.array([[1, 2], [3, 4]], dtype="uint8"), 1)
    payload = mem.read()
    client = TestClient(app)
    response = client.post(
        "/api/v1/data-assets/upload",
        headers={"Authorization": "Bearer test-secret-token"},
        files={"file": ("test.tif", payload, "image/tiff")},
    )
    assert response.status_code == 200, response.text
    asset = response.json()["asset"]
    assert asset["detected_format"] == "GeoTIFF"
    assert asset["is_raw"] is True
    assert asset["validation_status"] == "pending_scientific_validation"
    assert asset["detected_metadata"]["width"] == 2
    assert "storage_key" not in asset
    client.close()
    app.dependency_overrides.clear()
    engine.dispose()
    mem.close()
