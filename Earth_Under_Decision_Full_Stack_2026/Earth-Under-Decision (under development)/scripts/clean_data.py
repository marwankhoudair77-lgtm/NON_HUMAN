#!/usr/bin/env python3
"""Reproducible cleaning pipeline for the uploaded Nile Delta 2023 inputs.

This script never edits source files. It reads the original GLDAS CSV exports,
GPM IMERG GeoTIFF, and NOAA GHCN-Daily export and writes derived CSVs plus a
QC/provenance JSON into data/processed. NOAA is retained as external comparison
material and is not represented as NASA data.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import rasterio

YEAR = 2023
EXPECTED_GLDAS_STEPS_PER_DAY = 8


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def find_one(raw_dir: Path, patterns: list[str]) -> Path:
    matches: list[Path] = []
    for pattern in patterns:
        matches.extend(raw_dir.glob(pattern))
    matches = sorted(set(matches))
    if len(matches) != 1:
        raise FileNotFoundError(
            f"Expected exactly one raw file for patterns {patterns}; found {len(matches)}: "
            + ", ".join(p.name for p in matches)
        )
    return matches[0]


def read_gldas_series(path: Path, value_name: str) -> pd.DataFrame:
    frame = pd.read_csv(path)
    if not {"x", "y"}.issubset(frame.columns):
        raise ValueError(f"{path.name} must contain x (timestamp) and y (value) columns")
    frame = frame.rename(columns={"x": "timestamp", "y": value_name})
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True, errors="raise")
    if frame["timestamp"].duplicated().any():
        raise ValueError(f"Duplicate timestamps found in {path.name}")
    frame["date"] = frame["timestamp"].dt.tz_convert("UTC").dt.tz_localize(None).dt.normalize()
    if frame[value_name].isna().any():
        raise ValueError(f"Missing {value_name} values found in {path.name}; do not fill missing values with zero")
    return frame


def run(raw_dir: Path, out_dir: Path) -> dict[str, Any]:
    raw_dir = raw_dir.resolve()
    out_dir = out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    evap_path = find_one(raw_dir, ["*Evap_tavg*.csv"])
    root_path = find_one(raw_dir, ["*RootMoist_inst*.csv"])
    gpm_path = find_one(raw_dir, ["*GPM_3IMERGM*precipitation*.tif", "*GPM_3IMERGM*precipitation*.tiff"])
    noaa_path = find_one(raw_dir, ["4432340.csv", "noaa_ghcn_daily_egypt_2023.csv"])

    qc: dict[str, Any] = {
        "year": YEAR,
        "raw_files": {},
        "method": {
            "gldas_evapotranspiration": "Evap_tavg (kg m-2 s-1) multiplied by 10800 seconds per 3-hour interval, then summed by UTC calendar day; 1 kg m-2 water equivalent = 1 mm.",
            "gldas_root_moisture": "RootMoist_inst (kg m-2) summarized by UTC day using mean/min/max; retained in kg m-2 (numerically equivalent to mm water equivalent).",
            "gpm_precipitation": "GPM_3IMERGM v07 time-mean rate (mm/hr) from 2023 GeoTIFF. Annualized equivalent = mean rate × 24 × 365; this is not a directly summed daily/monthly accumulation product.",
            "noaa_reference": "NOAA GHCN-Daily is retained as an external reference only; it is not NASA data and is not mixed into NASA-only indicator results.",
        },
        "warnings": [
            "GLDAS point series represents one model grid point near 30.9 N, 31.0 E, not an area-average over the Nile Delta.",
            "The GPM GeoTIFF is GPM_3IMERGM monthly v07 and stores a temporal-mean rate in mm/hr; annualized values are rate-equivalent estimates.",
            "NOAA station temperature is an external comparison source with incomplete Alexandria coverage; it must not be presented as NASA data.",
            "No NDVI or MODIS LST input files were supplied in this data batch.",
            "The 2023 record supports seasonal description within one year, not long-term climate trend or future forecast claims.",
        ],
    }

    for label, path in {
        "gldas_evap_raw": evap_path,
        "gldas_root_moisture_raw": root_path,
        "gpm_imerg_geotiff": gpm_path,
        "noaa_ghcn_daily_raw": noaa_path,
    }.items():
        qc["raw_files"][label] = {"filename": path.name, "size_bytes": path.stat().st_size, "sha256": sha256(path)}

    # GLDAS 3-hourly exports -> daily summaries. Keep UTC calendar dates explicit.
    evap = read_gldas_series(evap_path, "evap_flux_kg_m2_s")
    root = read_gldas_series(root_path, "root_moisture_kg_m2")
    if not evap["timestamp"].equals(root["timestamp"]):
        raise ValueError("GLDAS Evap_tavg and RootMoist_inst timestamps do not align exactly")

    date_index = pd.date_range(f"{YEAR}-01-01", f"{YEAR}-12-31", freq="D", name="date")
    evap = evap[(evap["date"] >= date_index.min()) & (evap["date"] <= date_index.max())].copy()
    root = root[(root["date"] >= date_index.min()) & (root["date"] <= date_index.max())].copy()

    evap["evap_mm_per_3h"] = evap["evap_flux_kg_m2_s"] * 10800.0
    evap_daily = evap.groupby("date").agg(
        et_mm_day=("evap_mm_per_3h", "sum"),
        gldas_steps_per_day=("evap_mm_per_3h", "size"),
        et_negative_steps=("evap_mm_per_3h", lambda values: int((values < 0).sum())),
    )
    root_daily = root.groupby("date").agg(
        rootmoist_mm_mean=("root_moisture_kg_m2", "mean"),
        rootmoist_mm_min=("root_moisture_kg_m2", "min"),
        rootmoist_mm_max=("root_moisture_kg_m2", "max"),
    )
    gldas = evap_daily.join(root_daily).reindex(date_index)
    missing_days = int(gldas["gldas_steps_per_day"].isna().sum())
    bad_step_days = int((gldas["gldas_steps_per_day"] != EXPECTED_GLDAS_STEPS_PER_DAY).sum())
    if missing_days or bad_step_days:
        raise ValueError(f"GLDAS daily coverage failed: missing_days={missing_days}, not_8_steps={bad_step_days}")

    # NOAA GHCN-Daily comparison table; missing observations remain null.
    weather = pd.read_csv(noaa_path)
    required = {"STATION", "NAME", "DATE", "PRCP", "TAVG", "TMAX", "TMIN"}
    if not required.issubset(weather.columns):
        raise ValueError(f"NOAA file missing required columns: {sorted(required - set(weather.columns))}")
    weather["DATE"] = pd.to_datetime(weather["DATE"], errors="raise")
    weather = weather.rename(columns={
        "STATION": "station_id", "NAME": "station_name", "DATE": "date",
        "PRCP": "prcp_mm", "TAVG": "tavg_c", "TMAX": "tmax_c", "TMIN": "tmin_c",
    })
    duplicate_station_days = int(weather.duplicated(["station_id", "date"]).sum())
    if duplicate_station_days:
        raise ValueError(f"NOAA contains {duplicate_station_days} duplicate station/date records")
    weather["flag_tmax_lt_tmin"] = weather["tmax_c"] < weather["tmin_c"]
    weather["flag_tavg_outside_range"] = (
        (weather["tavg_c"] > weather["tmax_c"] + 0.5)
        | (weather["tavg_c"] < weather["tmin_c"] - 0.5)
    )
    weather["in_nile_delta_region"] = weather["station_name"].str.startswith("ALEXANDRIA", na=False)
    weather = weather.sort_values(["station_name", "date"])
    weather.to_csv(out_dir / "weather_stations_2023_clean.csv", index=False, float_format="%.2f")

    alex = weather[weather["in_nile_delta_region"]].set_index("date")[["tavg_c", "tmax_c", "tmin_c", "prcp_mm"]].add_prefix("alex_").reindex(date_index)
    daily = gldas.join(alex)
    daily["month"] = daily.index.month
    daily["lat"] = 30.9
    daily["lon"] = 31.0
    daily = daily.reset_index()
    daily["et_mm_day"] = daily["et_mm_day"].round(4)
    for column in ["rootmoist_mm_mean", "rootmoist_mm_min", "rootmoist_mm_max"]:
        daily[column] = daily[column].round(3)
    daily["gldas_steps_per_day"] = daily["gldas_steps_per_day"].astype("Int64")
    daily["et_negative_steps"] = daily["et_negative_steps"].astype("Int64")
    daily.to_csv(out_dir / "nile_delta_daily_clean_2023.csv", index=False)

    monthly = daily.groupby("month").agg(
        et_mm_month=("et_mm_day", "sum"),
        rootmoist_mm_mean=("rootmoist_mm_mean", "mean"),
        rootmoist_mm_min=("rootmoist_mm_min", "min"),
        rootmoist_mm_max=("rootmoist_mm_max", "max"),
        alex_tavg_c_mean=("alex_tavg_c", "mean"),
        alex_days_with_data=("alex_tavg_c", "count"),
    ).round(2)
    monthly.to_csv(out_dir / "storytelling_monthly_summary_2023.csv")

    # GPM GeoTIFF: use actual geotransform/CRS/NoData, not hard-coded coordinates.
    with rasterio.open(gpm_path) as raster:
        if raster.count < 1:
            raise ValueError("GPM GeoTIFF contains no raster bands")
        band = raster.read(1, masked=True).astype("float64")
        values = band.filled(np.nan)
        rows, cols = np.indices(values.shape)
        xs, ys = rasterio.transform.xy(raster.transform, rows, cols, offset="center")
        grid = pd.DataFrame({
            "lat": np.round(np.asarray(ys).reshape(-1), 3),
            "lon": np.round(np.asarray(xs).reshape(-1), 3),
            "precip_mm_hr_mean_2023": values.reshape(-1),
        })
        grid = grid.dropna(subset=["precip_mm_hr_mean_2023"]).copy()
        grid["precip_mm_year_2023"] = grid["precip_mm_hr_mean_2023"] * 24.0 * 365.0
        grid.to_csv(out_dir / "gpm_imerg_precip_2023_grid_clean.csv", index=False, float_format="%.5f")
        raster_meta = {
            "driver": raster.driver,
            "crs": str(raster.crs) if raster.crs else None,
            "width": raster.width,
            "height": raster.height,
            "count": raster.count,
            "resolution_degrees": list(raster.res),
            "bounds": [raster.bounds.left, raster.bounds.bottom, raster.bounds.right, raster.bounds.top],
            "nodata": raster.nodata,
            "band_tags": raster.tags(1),
            "global_tags": raster.tags(),
        }

    alex_rows = daily[daily["alex_tavg_c"].notna()]
    nearby = grid[
        grid["lat"].between(30.85, 31.15) & grid["lon"].between(30.85, 31.15)
    ]
    qc.update({
        "gldas": {
            "daily_rows": int(len(daily)),
            "gldas_steps_per_day_values": sorted(daily["gldas_steps_per_day"].dropna().astype(int).unique().tolist()),
            "missing_days": missing_days,
            "days_not_equal_to_8_steps": bad_step_days,
            "daily_et_negative_days": int((daily["et_mm_day"] < 0).sum()),
            "negative_three_hour_steps": int(daily["et_negative_steps"].sum()),
            "et_net_sum_2023_mm_at_point": round(float(daily["et_mm_day"].sum()), 4),
            "root_moisture_mean_kg_m2": round(float(daily["rootmoist_mm_mean"].mean()), 4),
            "root_moisture_min_kg_m2": round(float(daily["rootmoist_mm_min"].min()), 4),
            "root_moisture_min_date": str(daily.loc[daily["rootmoist_mm_min"].idxmin(), "date"]),
            "root_moisture_max_kg_m2": round(float(daily["rootmoist_mm_max"].max()), 4),
            "root_moisture_max_date": str(daily.loc[daily["rootmoist_mm_max"].idxmax(), "date"]),
            "grid_point_lat": 30.9,
            "grid_point_lon": 31.0,
        },
        "gpm": {
            "raster_metadata": raster_meta,
            "valid_grid_cells": int(len(grid)),
            "annualized_equivalent_mean_mm_year": round(float(grid["precip_mm_year_2023"].mean()), 4),
            "annualized_equivalent_min_mm_year": round(float(grid["precip_mm_year_2023"].min()), 4),
            "annualized_equivalent_max_mm_year": round(float(grid["precip_mm_year_2023"].max()), 4),
            "annualized_equivalent_mean_near_gldas_point_mm_year": round(float(nearby["precip_mm_year_2023"].mean()), 4) if not nearby.empty else None,
        },
        "noaa_reference": {
            "station_count": int(weather["station_id"].nunique()),
            "alexandria_records": int(len(alex_rows)),
            "alexandria_first_date": str(alex_rows["date"].min().date()) if not alex_rows.empty else None,
            "alexandria_last_date": str(alex_rows["date"].max().date()) if not alex_rows.empty else None,
            "alexandria_tavg_days": int(alex_rows["alex_tavg_c"].count()),
            "duplicate_station_days": duplicate_station_days,
            "tmax_lt_tmin_flags": int(weather["flag_tmax_lt_tmin"].sum()),
            "tavg_outside_range_flags": int(weather["flag_tavg_outside_range"].sum()),
        },
    })

    (out_dir / "qc_report_2023.json").write_text(json.dumps(qc, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return qc


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=Path("data/raw"), help="Directory containing uploaded raw source files")
    parser.add_argument("--out-dir", type=Path, default=Path("data/processed"), help="Directory for derived clean outputs")
    args = parser.parse_args()
    report = run(args.raw_dir, args.out_dir)
    print(json.dumps(report, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
