from app.core.config import get_settings
from app.storage.local import LocalStorage


def get_storage():
    backend = get_settings().storage_backend.lower()
    if backend == "local":
        return LocalStorage()
    if backend == "s3":
        raise NotImplementedError("S3-compatible storage is an architectural extension point but is not implemented in this MVP.")
    raise ValueError(f"Unsupported STORAGE_BACKEND: {backend}")
