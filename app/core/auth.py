import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.supabase import get_admin_client, get_user_client

security = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AuthContext:
    user_id: str
    auth_type: str  # "jwt" | "api_key"
    api_key_id: str | None = None
    access_token: str | None = None


def hash_api_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


async def verify_api_key(key: str) -> AuthContext:
    if not key.startswith("pi_"):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="无效 API Key")

    admin = get_admin_client()
    key_hash = hash_api_key(key)
    result = (
        admin.table("api_keys")
        .select("id, user_id")
        .eq("key_hash", key_hash)
        .maybe_single()
        .execute()
    )
    data = result.data
    if not data:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="无效 API Key")

    admin.table("api_keys").update(
        {"last_used_at": datetime.now(UTC).isoformat()}
    ).eq("id", data["id"]).execute()

    return AuthContext(
        user_id=data["user_id"],
        auth_type="api_key",
        api_key_id=data["id"],
    )


async def verify_supabase_jwt(token: str) -> AuthContext:
    client = get_user_client(token)
    try:
        response = client.auth.get_user(token)
    except Exception as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="无效或过期 Token") from exc

    user = response.user
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="未登录")

    return AuthContext(
        user_id=user.id,
        auth_type="jwt",
        access_token=token,
    )


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
) -> AuthContext:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail="需要 Bearer Token（Supabase JWT 或 pi_ API Key）",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials.strip()
    if token.startswith("pi_"):
        return await verify_api_key(token)
    return await verify_supabase_jwt(token)
