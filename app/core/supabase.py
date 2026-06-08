from functools import lru_cache

from supabase import Client, create_client

from app.config import get_settings


@lru_cache
def get_admin_client() -> Client:
    settings = get_settings()
    return create_client(
        settings.supabase_url,
        settings.supabase_service_role_key,
        options=None,
    )


def get_user_client(access_token: str) -> Client:
    """创建带用户 JWT 的 Supabase 客户端，RLS 按用户生效。"""
    settings = get_settings()
    client = create_client(settings.supabase_url, settings.supabase_anon_key)
    client.postgrest.auth(access_token)
    return client
