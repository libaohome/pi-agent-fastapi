import pytest

from app.services.playwright_sandbox import SandboxError, validate_target_url


def test_block_localhost(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "test")
    from app.config import get_settings

    get_settings.cache_clear()

    with pytest.raises(SandboxError, match="localhost"):
        validate_target_url("http://localhost:3000")


def test_block_private_ip(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "test")
    from app.config import get_settings

    get_settings.cache_clear()

    with pytest.raises(SandboxError):
        validate_target_url("http://192.168.1.1/admin")


def test_allow_public_https(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "test")
    from app.config import get_settings

    get_settings.cache_clear()

    assert validate_target_url("https://example.com/path") == "https://example.com/path"
