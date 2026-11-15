from pathlib import Path
from typing import Any
import rasterio
import h5py
import xarray as xr

TIFF_SIGNATURES = (b"II*\x00", b"MM\x00*", b"II+\x00", b"MM\x00+")
HDF5_SIGNATURE = b"\x89HDF\r\n\x1a\n"
HDF4_SIGNATURE = b"\x0e\x03\x13\x01"
NETCDF_SIGNATURES = (b"CDF\x01", b"CDF\x02", b"CDF\x05")


class UnsupportedRasterFormat(ValueError):
    pass


def detect_format(path: Path, filename: str) -> str:
    with path.open("rb") as stream:
        header = stream.read(8192)
    lower = filename.lower()
    if any(header.startswith(signature) for signature in TIFF_SIGNATURES):
        return "GeoTIFF"
    if any(header.startswith(signature) for signature in NETCDF_SIGNATURES):
        return "NetCDF"
    if header.find(HDF4_SIGNATURE) >= 0 and lower.endswith((".hdf", ".h4")):
        return "HDF4"
    # HDF5 permits a user block before the superblock signature (commonly 512-byte offsets).
    if header.find(HDF5_SIGNATURE) >= 0:
        return "NetCDF4" if lower.endswith((".nc", ".nc4")) else "HDF5"
    raise UnsupportedRasterFormat("File signature is not a supported GeoTIFF, HDF5/HDF, or NetCDF format.")


def _safe_scalar(value: Any) -> Any:
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            return str(value)
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def inspect_file(path: Path, detected_format: str) -> tuple[dict, list[str]]:
    warnings: list[str] = []
    if detected_format == "GeoTIFF":
        return _inspect_rasterio(path), warnings
    if detected_format == "NetCDF":
        try:
            return _inspect_xarray(path), warnings
        except Exception as exc:
            warnings.append(f"NetCDF metadata could not be fully inspected: {type(exc).__name__}")
            return {"format": detected_format, "metadata_inspection": "incomplete"}, warnings
    if detected_format in {"HDF5", "NetCDF4"}:
        metadata = _inspect_hdf5(path, detected_format)
        try:
            raster_metadata = _inspect_rasterio(path)
            metadata["raster_subdatasets"] = raster_metadata.get("subdatasets", [])
        except Exception:
            pass
        return metadata, warnings
    if detected_format == "HDF4":
        return _inspect_hdf4(path, warnings), warnings
    raise UnsupportedRasterFormat("Unsupported format.")


def _inspect_rasterio(path: Path) -> dict:
    with rasterio.open(path) as dataset:
        bounds = dataset.bounds
        metadata = {
            "format": "GeoTIFF",
            "driver": dataset.driver,
            "width": dataset.width,
            "height": dataset.height,
            "band_count": dataset.count,
            "crs": str(dataset.crs) if dataset.crs else None,
            "bounds": [float(bounds.left), float(bounds.bottom), float(bounds.right), float(bounds.top)],
            "transform": [float(v) for v in dataset.transform],
            "resolution": [abs(float(dataset.res[0])), abs(float(dataset.res[1]))],
            "dtypes": list(dataset.dtypes),
            "nodata_values": [_safe_scalar(value) for value in dataset.nodatavals],
            "band_descriptions": list(dataset.descriptions),
            "subdatasets": list(dataset.subdatasets),
            "tags": {k: str(v)[:500] for k, v in dataset.tags().items() if k.lower() not in {"password", "token", "authorization"}},
        }
        return metadata


def _inspect_xarray(path: Path) -> dict:
    with xr.open_dataset(path, decode_times=False, cache=False) as dataset:
        return {
            "format": "NetCDF",
            "dimensions": {key: int(value) for key, value in dataset.sizes.items()},
            "coordinates": list(dataset.coords),
            "variables": list(dataset.data_vars),
            "global_attributes": {str(k): _safe_scalar(v) for k, v in dataset.attrs.items()},
            "variable_metadata": {
                key: {
                    "dimensions": list(value.dims),
                    "shape": [int(x) for x in value.shape],
                    "dtype": str(value.dtype),
                    "units": _safe_scalar(value.attrs.get("units")),
                    "long_name": _safe_scalar(value.attrs.get("long_name")),
                }
                for key, value in dataset.data_vars.items()
            },
        }


def _inspect_hdf5(path: Path, detected_format: str) -> dict:
    items: list[dict] = []
    with h5py.File(path, "r") as handle:
        def visitor(name, obj):
            if isinstance(obj, h5py.Dataset):
                items.append({"name": name, "shape": [int(v) for v in obj.shape], "dtype": str(obj.dtype)})
        handle.visititems(visitor)
        root_attrs = {str(k): _safe_scalar(v) for k, v in handle.attrs.items()}
    return {
        "format": detected_format,
        "top_level_groups": [],
        "datasets": items[:500],
        "dataset_count_captured": min(len(items), 500),
        "root_attributes": root_attrs,
    }


def _inspect_hdf4(path: Path, warnings: list[str]) -> dict:
    try:
        from pyhdf.SD import SD, SDC  # optional HDF4 reader
        handle = SD(str(path), SDC.READ)
        try:
            datasets = []
            for name, info in handle.datasets().items():
                datasets.append({"name": name, "shape": [int(v) for v in info[0]], "rank": int(info[1]), "type": str(info[3])})
            attributes = {str(k): _safe_scalar(v) for k, v in handle.attributes().items()}
            return {"format": "HDF4", "datasets": datasets, "root_attributes": attributes}
        finally:
            handle.end()
    except ImportError:
        warnings.append("HDF4 signature recognized, but PyHDF is not installed; metadata inspection is pending. The original file was preserved.")
        return {"format": "HDF4", "metadata_inspection": "pending_optional_reader"}
    except Exception as exc:
        warnings.append(f"HDF4 metadata inspection failed: {type(exc).__name__}; the original file was preserved.")
        return {"format": "HDF4", "metadata_inspection": "incomplete", "error_type": type(exc).__name__}
