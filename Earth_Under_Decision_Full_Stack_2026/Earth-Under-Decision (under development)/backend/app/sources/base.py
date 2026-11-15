from dataclasses import dataclass
from typing import Protocol, Any


@dataclass(frozen=True)
class ConnectorStatus:
    key: str
    configured: bool
    implemented: bool
    status: str
    message: str


class DataSourceAdapter(Protocol):
    key: str

    def status(self) -> ConnectorStatus: ...

    def submit_acquisition(self, request: dict[str, Any]) -> str:
        """Return a real provider task identifier, or raise when unsupported."""
        ...


class PendingAdapter:
    """Explicit placeholder: never simulates an upstream download."""

    def __init__(self, key: str, message: str):
        self.key = key
        self.message = message

    def status(self) -> ConnectorStatus:
        return ConnectorStatus(
            key=self.key,
            configured=False,
            implemented=False,
            status="pending_connector_verification",
            message=self.message,
        )

    def submit_acquisition(self, request: dict[str, Any]) -> str:
        raise NotImplementedError("This official-source connector has not been implemented and verified.")
