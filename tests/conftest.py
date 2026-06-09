import pytest
from fastapi.testclient import TestClient

from app.core.auth import AuthContext, get_current_user
from app.main import app

MOCK_USER = AuthContext(user_id="test-user-id", auth_type="jwt", access_token="test-token")


async def _mock_get_current_user() -> AuthContext:
    return MOCK_USER


@pytest.fixture(autouse=True)
def _test_env(monkeypatch, tmp_path):
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test-anon-key")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "test-service-key")
    monkeypatch.setenv("KNOWLEDGE_GRAPH_DIR", str(tmp_path / "knowledge-graphs"))
    from app.config import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
    app.dependency_overrides.clear()


@pytest.fixture
def auth_client():
    app.dependency_overrides[get_current_user] = _mock_get_current_user
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
def anon_client():
    app.dependency_overrides.clear()
    with TestClient(app) as client:
        yield client
