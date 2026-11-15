from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
import app.services.story_data as story_data

PROJECT_DATA = Path(__file__).resolve().parents[2] / "data"


def test_storytelling_summary_uses_uploaded_cleaned_files(monkeypatch):
    monkeypatch.setattr(story_data, "data_root", lambda: PROJECT_DATA)
    client = TestClient(app)
    response = client.get("/api/v1/storytelling/summary")
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["data_inventory"]["gldas_daily_rows"] == 365
    assert payload["data_inventory"]["gpm_valid_grid_cells"] == 540
    assert payload["data_inventory"]["ndvi_available"] is False
    assert payload["data_inventory"]["lst_available"] is False
    assert abs(payload["metrics"]["evapotranspiration"]["value"] - 89.79) < 0.1
    assert payload["metrics"]["precipitation"]["product_id"] == "GPM_3IMERGM"
    assert "annualized" in payload["metrics"]["precipitation"]["units"]
    client.close()


def test_storytelling_monthly_and_map_grid(monkeypatch):
    monkeypatch.setattr(story_data, "data_root", lambda: PROJECT_DATA)
    client = TestClient(app)
    monthly = client.get("/api/v1/storytelling/monthly")
    grid = client.get("/api/v1/storytelling/precipitation-grid")
    assert monthly.status_code == 200
    assert len(monthly.json()["series"]) == 12
    assert monthly.json()["series"][0]["root_moisture_month_min_kg_m2"] == 106.37
    assert monthly.json()["series"][0]["root_moisture_month_max_kg_m2"] == 111.86
    assert monthly.json()["interpretation"].lower().find("not a long-term") >= 0
    assert grid.status_code == 200
    assert grid.json()["cell_count"] == 540
    assert grid.json()["features"][0]["geometry"]["type"] == "Point"
    client.close()


def test_noaa_reference_is_kept_separate(monkeypatch):
    monkeypatch.setattr(story_data, "data_root", lambda: PROJECT_DATA)
    client = TestClient(app)
    catalog = client.get("/api/v1/storytelling/catalog").json()["items"]
    noaa = next(item for item in catalog if item["indicator"] == "air_temperature_reference")
    assert "NASA-only evidence" in noaa["notes"]
    assert noaa["status"] == "external_reference_incomplete"
    client.close()
