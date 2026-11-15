from pathlib import Path
from uuid import uuid4
from app.core.config import get_settings


class LocalStorage:
    def __init__(self, root: Path | None = None):
        configured = root or get_settings().local_storage_root
        self.root = configured.expanduser().resolve()

    def create_raw_temp_file(self) -> tuple[Path, str]:
        temp_dir = self.root / "tmp"
        temp_dir.mkdir(parents=True, exist_ok=True)
        name = f"{uuid4().hex}.upload"
        path = temp_dir / name
        self._assert_inside_root(path)
        return path, name

    def commit_raw(self, temp_path: Path, file_extension: str) -> str:
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        relative = Path("raw") / now.strftime("%Y") / now.strftime("%m") / f"{uuid4().hex}{file_extension.lower()}"
        destination = self.root / relative
        self._assert_inside_root(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        temp_path.replace(destination)
        try:
            destination.chmod(0o444)
        except OSError:
            pass
        return relative.as_posix()

    def resolve(self, storage_key: str) -> Path:
        candidate = (self.root / storage_key).resolve()
        self._assert_inside_root(candidate)
        return candidate

    def delete_temp(self, path: Path) -> None:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass

    def _assert_inside_root(self, path: Path) -> None:
        root = self.root.resolve()
        resolved = path.resolve()
        if not resolved.is_relative_to(root):
            raise ValueError("Storage path escapes the configured storage root.")
