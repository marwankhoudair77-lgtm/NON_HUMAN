from app.sources.base import PendingAdapter

ADAPTERS = {
    "nasa_appeears": PendingAdapter(
        "nasa_appeears",
        "AppEEARS request/response flow, credentials, and product parameters require official-documentation verification.",
    ),
    "nasa_gesdisc": PendingAdapter(
        "nasa_gesdisc",
        "GPM Earthdata download flow, release metadata, authentication, and file integrity require verification.",
    ),
}


def connector_statuses() -> list[dict]:
    return [adapter.status().__dict__ for adapter in ADAPTERS.values()]
