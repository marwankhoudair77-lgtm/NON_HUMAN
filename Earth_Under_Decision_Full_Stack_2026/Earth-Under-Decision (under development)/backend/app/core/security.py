import hmac
from fastapi import Header, HTTPException, status
from app.core.config import get_settings


def require_admin_token(authorization: str | None = Header(default=None)) -> None:
    settings = get_settings()
    expected = settings.admin_api_token
    if not expected or expected in {"CHANGE_ME", "CHANGE_ME_TO_A_LONG_RANDOM_SECRET"}:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "admin_token_not_configured", "message": "Administrative operations are disabled until ADMIN_API_TOKEN is configured."},
        )
    scheme, _, supplied = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not supplied or not hmac.compare_digest(supplied, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "unauthorized", "message": "A valid administrative bearer token is required."},
            headers={"WWW-Authenticate": "Bearer"},
        )
