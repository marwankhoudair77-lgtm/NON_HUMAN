from pathlib import Path
import pytest
from app.geospatial.inspect import detect_format, UnsupportedRasterFormat
from app.storage.local import LocalStorage


def test_detects_supported_file_signatures(tmp_path: Path):
    path = tmp_path / "observations.tif"
    path.write_bytes(b"II*\x00" + b"\x00" * 16)
    assert detect_format(path, path.name) == "GeoTIFF"


def test_rejects_unknown_signature(tmp_path: Path):
    path = tmp_path / "fake.tif"
    path.write_bytes(b"not-a-raster")
    with pytest.raises(UnsupportedRasterFormat):
        detect_format(path, path.name)


def test_storage_blocks_path_traversal(tmp_path: Path):
    storage = LocalStorage(tmp_path / "store")
    with pytest.raises(ValueError):
        storage.resolve("../../secrets.txt")


def test_detects_hdf4_signature(tmp_path: Path):
    path = tmp_path / "modis.hdf"
    path.write_bytes(b"\x0e\x03\x13\x01" + b"\x00" * 40)
    assert detect_format(path, path.name) == "HDF4"
