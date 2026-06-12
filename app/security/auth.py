from dataclasses import dataclass
import hashlib
import hmac
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status

from app.config import get_settings


ROLE_LEVELS = {
    "viewer": 10,
    "auditor": 20,
    "compliance_reviewer": 30,
    "admin": 40,
}


@dataclass(frozen=True)
class AuthenticatedUser:
    subject: str
    role: str
    auth_mode: str
    tenant_id: str


def _extract_bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    return token.strip()


def _validate_role(role: str) -> str:
    normalized = role.strip().lower()
    if normalized not in ROLE_LEVELS:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unsupported user role")
    return normalized


def _valid_api_key(provided_key: str | None, configured_key: str | None, configured_hash: str | None) -> bool:
    if not provided_key:
        return False
    if configured_hash:
        digest = hashlib.sha256(provided_key.encode("utf-8")).hexdigest()
        return hmac.compare_digest(digest, configured_hash.strip().lower())
    if configured_key:
        return hmac.compare_digest(provided_key, configured_key)
    return False


def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
    x_user: Annotated[str | None, Header(alias="X-User")] = None,
    x_user_role: Annotated[str | None, Header(alias="X-User-Role")] = None,
    x_tenant_id: Annotated[str | None, Header(alias="X-Tenant-ID")] = None,
) -> AuthenticatedUser:
    settings = get_settings()
    tenant_id = (x_tenant_id or settings.default_tenant_id).strip() or "default"
    if settings.auth_mode == "disabled":
        return AuthenticatedUser(
            subject=x_user or "local-dev",
            role=_validate_role(x_user_role or settings.default_user_role),
            auth_mode="disabled",
            tenant_id=tenant_id,
        )

    if settings.auth_mode != "api_key":
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unsupported auth mode")
    if not settings.platform_api_key and not settings.platform_api_key_sha256:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="PLATFORM_API_KEY or PLATFORM_API_KEY_SHA256 is not configured",
        )

    provided_key = x_api_key or _extract_bearer_token(authorization)
    if not _valid_api_key(provided_key, settings.platform_api_key, settings.platform_api_key_sha256):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing API key")

    return AuthenticatedUser(
        subject=x_user or "api-key-user",
        role=_validate_role(x_user_role or settings.default_user_role),
        auth_mode="api_key",
        tenant_id=tenant_id,
    )


def require_roles(*roles: str):
    minimum = min(ROLE_LEVELS[_validate_role(role)] for role in roles)

    def dependency(user: Annotated[AuthenticatedUser, Depends(get_current_user)]) -> AuthenticatedUser:
        if ROLE_LEVELS[user.role] < minimum:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
        return user

    return dependency
