from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import HTTPException

from app.core.config import get_settings


def data_root() -> Path:
    root = get_settings().local_storage_root.expanduser()
    return root.resolve()


def processed_file(name: str) -> Path:
    path = data_root() / "processed" / name
    if not path.exists():
        raise HTTPException(
            status_code=503,
            detail={
                "code": "processed_dataset_missing",
                "message": f"Required processed project data is not available: {name}",
            },
        )
    return path


@lru_cache(maxsize=8)
def _csv(name: str, modified_ns: int) -> pd.DataFrame:
    # The mtime argument invalidates the cache when a new clean run replaces a file.
    return pd.read_csv(processed_file(name))


def load_csv(name: str) -> pd.DataFrame:
    path = processed_file(name)
    return _csv(name, path.stat().st_mtime_ns).copy()


def load_qc() -> dict[str, Any]:
    path = data_root() / "processed" / "qc_report_2023.json"
    if not path.exists():
        return {"status": "not_available", "message": "QC report is not present."}
    return json.loads(path.read_text(encoding="utf-8"))


def build_summary() -> dict[str, Any]:
    daily = load_csv("nile_delta_daily_clean_2023.csv")
    monthly = load_csv("storytelling_monthly_summary_2023.csv")
    grid = load_csv("gpm_imerg_precip_2023_grid_clean.csv")
    qc = load_qc()

    daily["date"] = pd.to_datetime(daily["date"], errors="coerce")
    valid_station_days = int(daily["alex_tavg_c"].count()) if "alex_tavg_c" in daily else 0
    et_total = float(daily["et_mm_day"].sum())
    root_mean = float(daily["rootmoist_mm_mean"].mean())
    gpm_rate_mean = float(grid["precip_mm_hr_mean_2023"].mean())
    gpm_annualized = float(grid["precip_mm_year_2023"].mean())
    gpm_near = grid[
        grid["lat"].between(30.85, 31.15) & grid["lon"].between(30.85, 31.15)
    ]

    month_et = monthly.loc[monthly["et_mm_month"].idxmax()]
    min_root_date = daily.loc[daily["rootmoist_mm_min"].idxmin(), "date"]
    max_root_date = daily.loc[daily["rootmoist_mm_max"].idxmax(), "date"]

    return {
        "data_status": "available_with_limitations",
        "period": {"start": "2023-01-01", "end": "2023-12-31", "year": 2023},
        "study_area": {
            "name": "Nile Delta pilot context",
            "gldas_point": {"lat": 30.9, "lon": 31.0},
            "gpm_grid_bounds": {"west": float(grid["lon"].min() - 0.05), "south": float(grid["lat"].min() - 0.05), "east": float(grid["lon"].max() + 0.05), "north": float(grid["lat"].max() + 0.05)},
            "boundary_status": "not_provided_or_validated",
        },
        "metrics": {
            "evapotranspiration": {
                "value": round(et_total, 2),
                "units": "mm net modelled water-equivalent over 2023",
                "label": "GLDAS net evapotranspiration accumulation at one model grid point",
                "product_id": "GLDAS_NOAH025_3H",
                "version": "2.1",
                "native_frequency": "3-hourly",
                "daily_records": int(len(daily)),
                "point": {"lat": 30.9, "lon": 31.0},
                "peak_month": int(month_et["month"]),
                "peak_month_value_mm": round(float(month_et["et_mm_month"]), 2),
                "negative_flux_days": int((daily["et_mm_day"] < 0).sum()),
                "status": "processed_from_uploaded_source_export_scientific_review_pending",
                "interpretation": "Modelled natural-condition response, not measured irrigated-field water consumption.",
            },
            "root_zone_soil_moisture": {
                "value": round(root_mean, 2),
                "units": "kg m-2 (water-equivalent; numerically comparable to mm)",
                "label": "GLDAS root-zone soil moisture mean at one model grid point",
                "product_id": "GLDAS_NOAH025_3H",
                "version": "2.1",
                "native_frequency": "3-hourly; daily mean/min/max derived",
                "daily_records": int(len(daily)),
                "minimum": round(float(daily["rootmoist_mm_min"].min()), 2),
                "minimum_date": str(pd.Timestamp(min_root_date).date()),
                "maximum": round(float(daily["rootmoist_mm_max"].max()), 2),
                "maximum_date": str(pd.Timestamp(max_root_date).date()),
                "point": {"lat": 30.9, "lon": 31.0},
                "status": "processed_from_uploaded_source_export_scientific_review_pending",
                "interpretation": "Modelled root-zone state; not a direct field sensor observation or irrigation measurement.",
            },
            "precipitation": {
                "value": round(gpm_annualized, 2),
                "units": "annualized-equivalent mm/year",
                "label": "Mean annualized-equivalent precipitation across the supplied GPM grid",
                "mean_rate": round(gpm_rate_mean, 8),
                "mean_rate_units": "mm/hr",
                "minimum_annualized_equivalent": round(float(grid["precip_mm_year_2023"].min()), 2),
                "maximum_annualized_equivalent": round(float(grid["precip_mm_year_2023"].max()), 2),
                "near_gldas_point_annualized_equivalent": round(float(gpm_near["precip_mm_year_2023"].mean()), 2) if not gpm_near.empty else None,
                "grid_cells": int(len(grid)),
                "grid_resolution": "0.1 degree",
                "product_id": "GPM_3IMERGM",
                "version": "07",
                "native_temporal_product": "monthly",
                "temporal_summary": "time mean over 2023",
                "status": "source_file_metadata_inspected_derived_rate_estimate_scientific_review_pending",
                "calculation": "time-mean precipitation rate (mm/hr) × 24 × 365 hours; not a direct sum of original daily/monthly accumulation files.",
            },
            "noaa_temperature_reference": {
                "value": None,
                "units": "°C",
                "label": "NOAA Alexandria station daily mean temperature — external comparison only",
                "source": "NOAA GHCN-Daily",
                "available_days": valid_station_days,
                "last_available_date": str(pd.Timestamp(daily.loc[daily["alex_tavg_c"].last_valid_index(), "date"]).date()) if valid_station_days else None,
                "status": "external_reference_incomplete_not_nasa",
            },
        },
        "data_inventory": {
            "gldas_daily_rows": int(len(daily)),
            "gldas_days_with_eight_3h_steps": int((daily["gldas_steps_per_day"] == 8).sum()),
            "gpm_valid_grid_cells": int(len(grid)),
            "noaa_station_count": int(qc.get("noaa_reference", {}).get("station_count", 0)),
            "noaa_alexandria_days": valid_station_days,
            "ndvi_available": False,
            "lst_available": False,
        },
        "limitations": [
            "GLDAS values describe one 0.25-degree model grid point near 30.9°N, 31.0°E, not a validated Nile Delta area average.",
            "The GLDAS evapotranspiration series is a model output and does not represent actual irrigation-driven agricultural consumption.",
            "GPM data supplied is GPM_3IMERGM monthly v07; the GeoTIFF is a time-mean rate in mm/hr. The displayed annualized equivalent is derived from that rate and is not a daily series.",
            "NOAA temperature data is external to NASA and the Alexandria station has incomplete coverage through 2023-08-09 only.",
            "NDVI (MOD13Q1) and LST (MOD11A2) files were not included in this upload batch and remain unavailable.",
            "A single calendar year supports within-year seasonal description only; no long-term trend, causal claim, or future forecast is inferred.",
            "No official administrative boundary file was supplied; map pixels are shown without claiming governorate boundaries.",
        ],
        "qc": {
            "report_available": qc.get("year") == 2023,
            "gldas_missing_days": qc.get("gldas", {}).get("missing_days"),
            "gldas_days_not_eight_steps": qc.get("gldas", {}).get("days_not_equal_to_8_steps"),
            "gpm_valid_cells": qc.get("gpm", {}).get("valid_grid_cells"),
            "noaa_duplicate_station_days": qc.get("noaa_reference", {}).get("duplicate_station_days"),
            "noaa_tmax_tmin_flags": qc.get("noaa_reference", {}).get("tmax_lt_tmin_flags"),
            "noaa_tavg_range_flags": qc.get("noaa_reference", {}).get("tavg_outside_range_flags"),
        },
    }


def monthly_series() -> dict[str, Any]:
    frame = load_csv("storytelling_monthly_summary_2023.csv")
    rows = []
    for row in frame.to_dict(orient="records"):
        rows.append({
            "month": int(row["month"]),
            "evapotranspiration_mm": float(row["et_mm_month"]) if pd.notna(row["et_mm_month"]) else None,
            "root_moisture_mean_kg_m2": float(row["rootmoist_mm_mean"]) if pd.notna(row["rootmoist_mm_mean"]) else None,
            "root_moisture_month_min_kg_m2": float(row["rootmoist_mm_min"]) if pd.notna(row["rootmoist_mm_min"]) else None,
            "root_moisture_month_max_kg_m2": float(row["rootmoist_mm_max"]) if pd.notna(row["rootmoist_mm_max"]) else None,
            "noaa_alexandria_tavg_c_mean": float(row["alex_tavg_c_mean"]) if pd.notna(row["alex_tavg_c_mean"]) else None,
            "noaa_alexandria_days": int(row["alex_days_with_data"]),
        })
    return {
        "data_status": "available_with_limitations",
        "period": {"start": "2023-01", "end": "2023-12", "frequency": "monthly_summary_of_daily_GLDAS_and_partial_NOAA_reference"},
        "series": rows,
        "interpretation": "Within-year seasonal profile only; not a long-term trend or forecast.",
    }


def daily_series(variable: str, start: str | None = None, end: str | None = None) -> dict[str, Any]:
    allowed = {"evapotranspiration", "root_moisture", "noaa_air_temperature"}
    if variable not in allowed:
        raise HTTPException(status_code=422, detail={"code": "unsupported_variable", "message": f"variable must be one of {sorted(allowed)}"})
    frame = load_csv("nile_delta_daily_clean_2023.csv")
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
    start_dt = pd.Timestamp(start) if start else pd.Timestamp("2023-01-01")
    end_dt = pd.Timestamp(end) if end else pd.Timestamp("2023-12-31")
    if start_dt > end_dt:
        raise HTTPException(status_code=422, detail={"code": "invalid_date_range", "message": "start must be before or equal to end"})
    frame = frame[(frame["date"] >= start_dt) & (frame["date"] <= end_dt)]
    mapping = {
        "evapotranspiration": ("et_mm_day", "mm/day", "GLDAS modelled net evapotranspiration at a single grid point"),
        "root_moisture": ("rootmoist_mm_mean", "kg m-2", "GLDAS root-zone soil moisture daily mean at a single grid point"),
        "noaa_air_temperature": ("alex_tavg_c", "°C", "NOAA Alexandria station reference; not NASA; incomplete coverage"),
    }
    column, units, description = mapping[variable]
    rows = [
        {"date": row.date.strftime("%Y-%m-%d"), "value": float(row.value) if pd.notna(row.value) else None}
        for row in frame[["date", column]].rename(columns={column: "value"}).itertuples(index=False)
    ]
    return {
        "data_status": "available_with_gaps" if any(item["value"] is None for item in rows) else "available",
        "variable": variable,
        "units": units,
        "description": description,
        "point": {"lat": 30.9, "lon": 31.0} if variable != "noaa_air_temperature" else None,
        "series": rows,
        "count": len(rows),
        "valid_count": sum(item["value"] is not None for item in rows),
        "missing_values_are_null": True,
    }


def precipitation_geojson() -> dict[str, Any]:
    grid = load_csv("gpm_imerg_precip_2023_grid_clean.csv")
    features = []
    for row in grid.itertuples(index=False):
        rate = float(row.precip_mm_hr_mean_2023)
        annualized = float(row.precip_mm_year_2023)
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [float(row.lon), float(row.lat)]},
            "properties": {
                "precipitation_mean_rate_mm_hr": rate,
                "annualized_equivalent_mm_year": annualized,
                "product_id": "GPM_3IMERGM",
                "version": "07",
                "period": "2023-01-01/2023-12-31",
                "temporal_summary": "time mean",
                "status": "derived_rate_estimate_scientific_review_pending",
            },
        })
    return {
        "type": "FeatureCollection",
        "data_status": "available_with_limitations",
        "units": "annualized-equivalent mm/year",
        "grid_resolution": "0.1 degree",
        "cell_count": len(features),
        "note": "Points mark pixel centers of a 0.1-degree GPM_3IMERGM monthly v07 raster. Values are annualized equivalents derived from a 2023 time-mean rate, not daily accumulations. No administrative boundaries are included.",
        "features": features,
    }


def catalog() -> dict[str, Any]:
    return {
        "items": [
            {
                "id": "gpm-imerg-monthly-2023",
                "product_id": "GPM_3IMERGM",
                "version": "07",
                "indicator": "precipitation",
                "title": "GPM IMERG Monthly Final Run",
                "source": "NASA GPM / GES DISC",
                "status": "uploaded_and_metadata_inspected_scientific_review_pending",
                "period": "2023-01-01 to 2023-12-31 time-averaged map",
                "spatial_resolution": "0.1 degree",
                "temporal_resolution": "monthly product; time mean over selected year",
                "units": "mm/hr",
                "source_url": "https://gpm.nasa.gov/data/imerg",
                "notes": "Annualized-equivalent mm/year is derived from the time-mean rate; it is not a direct sum of daily precipitation files.",
            },
            {
                "id": "gldas-noah-evap-2023",
                "product_id": "GLDAS_NOAH025_3H",
                "version": "2.1",
                "indicator": "evapotranspiration",
                "title": "GLDAS Noah 3-hourly Evapotranspiration",
                "source": "NASA GES DISC",
                "status": "uploaded_and_processed_scientific_review_pending",
                "period": "2023-01-01 to 2023-12-31",
                "spatial_resolution": "0.25 degree model grid",
                "temporal_resolution": "3-hourly source; daily aggregate derived",
                "units": "kg m-2 s-1 source; mm/day derived",
                "source_url": "https://disc.gsfc.nasa.gov/datasets/GLDAS_NOAH025_3H_2.1/summary",
                "notes": "A single model grid point near 30.9 N, 31.0 E; not an area average or direct irrigation-consumption measurement.",
            },
            {
                "id": "gldas-noah-rootmoist-2023",
                "product_id": "GLDAS_NOAH025_3H",
                "version": "2.1",
                "indicator": "root_moisture",
                "title": "GLDAS Noah Root-zone Soil Moisture",
                "source": "NASA GES DISC",
                "status": "uploaded_and_processed_scientific_review_pending",
                "period": "2023-01-01 to 2023-12-31",
                "spatial_resolution": "0.25 degree model grid",
                "temporal_resolution": "3-hourly source; daily mean/min/max derived",
                "units": "kg m-2",
                "source_url": "https://disc.gsfc.nasa.gov/datasets/GLDAS_NOAH025_3H_2.1/summary",
                "notes": "Root-zone model state at one point; not a direct field sensor observation.",
            },
            {
                "id": "noaa-ghcn-alexandria-2023",
                "product_id": "GHCN-Daily",
                "version": None,
                "indicator": "air_temperature_reference",
                "title": "Alexandria Daily Weather Station Reference",
                "source": "NOAA NCEI (external; not NASA)",
                "status": "external_reference_incomplete",
                "period": "2023-01-01 to 2023-08-09 available for Alexandria mean temperature",
                "spatial_resolution": "station point",
                "temporal_resolution": "daily; incomplete station coverage",
                "units": "°C",
                "source_url": "https://www.ncei.noaa.gov/products/land-based-station/global-historical-climatology-network-daily",
                "notes": "Comparison-only source. Not part of NASA-only evidence.",
            },
            {
                "id": "mod13q1-pending",
                "product_id": "MOD13Q1",
                "version": "061",
                "indicator": "ndvi",
                "title": "Terra MODIS Vegetation Indices 16-Day",
                "source": "NASA LP DAAC",
                "status": "not_uploaded",
                "period": None,
                "spatial_resolution": "250 m nominal",
                "temporal_resolution": "16-day composite",
                "units": "dimensionless",
                "source_url": "https://lpdaac.usgs.gov/products/mod13q1v061/",
                "notes": "No MOD13Q1 data file was included in the current upload batch.",
            },
            {
                "id": "mod11a2-pending",
                "product_id": "MOD11A2",
                "version": "061",
                "indicator": "lst",
                "title": "Terra MODIS Land Surface Temperature 8-Day",
                "source": "NASA LP DAAC",
                "status": "not_uploaded",
                "period": None,
                "spatial_resolution": "1 km nominal",
                "temporal_resolution": "8-day composite",
                "units": "must be read from actual file metadata",
                "source_url": "https://lpdaac.usgs.gov/products/mod11a2v061/",
                "notes": "No MOD11A2 data file was included. Daytime and nighttime must remain separate.",
            },
        ],
        "count": 6,
    }
