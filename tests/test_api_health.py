import pytest


def test_health_ok(anon_client):
    resp = anon_client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "service" in data


@pytest.mark.parametrize(
    "path,method",
    [
        ("/api/v1/nlp/status", "get"),
        ("/api/v1/ocr/status", "get"),
        ("/api/v1/nlp/segment", "post"),
        ("/api/v1/knowledge-graph/graphs", "get"),
    ],
)
def test_protected_routes_require_auth(anon_client, path, method):
    if method == "post":
        resp = anon_client.post(path, json={})
    else:
        resp = anon_client.get(path)
    assert resp.status_code == 401
    assert "Bearer" in resp.json()["detail"]


def test_protected_routes_accept_mock_auth(auth_client):
    resp = auth_client.get("/api/v1/nlp/status")
    assert resp.status_code == 200
    assert "jieba" in resp.json()
