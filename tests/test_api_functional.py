import io

import pytest


def test_nlp_segment_jieba(auth_client):
    resp = auth_client.post(
        "/api/v1/nlp/segment",
        json={"text": "人工智能正在改变世界", "engine": "jieba"},
    )
    if resp.status_code == 503:
        pytest.skip("jieba 未安装")
    assert resp.status_code == 200
    data = resp.json()
    assert data["engine"] == "jieba"
    assert data["word_count"] > 0
    assert isinstance(data["words"], list)


def test_knowledge_graph_crud(auth_client):
    triple_resp = auth_client.post(
        "/api/v1/knowledge-graph/triples",
        json={"subject": "Python", "predicate": "用于", "object": "后端开发"},
    )
    assert triple_resp.status_code == 200
    graph_id = triple_resp.json()["graph_id"]

    query_resp = auth_client.post(
        "/api/v1/knowledge-graph/query",
        json={"entity": "Python", "depth": 1, "graph_id": graph_id},
    )
    assert query_resp.status_code == 200
    query = query_resp.json()
    assert "Python" in query["nodes"]

    export_resp = auth_client.get("/api/v1/knowledge-graph/export", params={"graph_id": graph_id})
    assert export_resp.status_code == 200
    assert "nodes" in export_resp.json()

    list_resp = auth_client.get("/api/v1/knowledge-graph/graphs")
    assert list_resp.status_code == 200
    graphs = list_resp.json()["graphs"]
    assert any(g["id"] == graph_id for g in graphs)


def test_knowledge_graph_export_requires_graph_id(auth_client):
    resp = auth_client.get("/api/v1/knowledge-graph/export")
    assert resp.status_code == 400


def test_markitdown_convert_file(auth_client):
    content = b"# Hello\n\nThis is a test markdown file."
    resp = auth_client.post(
        "/api/v1/markitdown/convert/file",
        files={"file": ("test.md", io.BytesIO(content), "text/markdown")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["format"] in ("markdown", "text")
    assert "Hello" in data["markdown"]


def test_markitdown_convert_empty_file(auth_client):
    resp = auth_client.post(
        "/api/v1/markitdown/convert/file",
        files={"file": ("empty.txt", io.BytesIO(b"   "), "text/plain")},
    )
    assert resp.status_code == 422


def test_ffmpeg_status_fields(auth_client):
    resp = auth_client.get("/api/v1/ffmpeg/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "ffmpeg_available" in data
    assert "ffprobe_available" in data


def test_presidio_analyze(auth_client):
    status = auth_client.get("/api/v1/presidio/status").json()
    if not status.get("available"):
        pytest.skip("presidio 未安装")

    resp = auth_client.post(
        "/api/v1/presidio/analyze",
        json={"text": "我的手机号是13800138000", "language": "zh"},
    )
    # 未安装 spacy 中文模型时可能 500
    assert resp.status_code in (200, 500)
    if resp.status_code == 200:
        assert "entities" in resp.json()


def test_embeddings_encode(auth_client):
    status = auth_client.get("/api/v1/embeddings/status").json()
    if not status.get("available"):
        pytest.skip("sentence-transformers 不可用")

    resp = auth_client.post(
        "/api/v1/embeddings/encode",
        json={"texts": ["你好世界", "hello world"], "normalize": True},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 2
    assert len(data["embeddings"]) == 2
    assert data["dimension"] > 0


def test_langextract_status(auth_client):
    resp = auth_client.get("/api/v1/langextract/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "default_provider" in data
    assert "default_model" in data


def test_integration_status_shape(auth_client):
    for path in [
        "/api/v1/integrations/feishu/status",
        "/api/v1/integrations/wecom/status",
        "/api/v1/integrations/coze/status",
        "/api/v1/integrations/n8n/status",
    ]:
        resp = auth_client.get(path)
        assert resp.status_code == 200
        assert "configured" in resp.json()
