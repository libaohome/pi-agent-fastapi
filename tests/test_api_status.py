import pytest

# 各模块 status 端点（需鉴权）
STATUS_ENDPOINTS = [
    "/api/v1/langextract/status",
    "/api/v1/playwright/status",
    "/api/v1/ytdlp/status",
    "/api/v1/ffmpeg/status",
    "/api/v1/ocr/status",
    "/api/v1/image/status",
    "/api/v1/pdf/status",
    "/api/v1/video-tools/status",
    "/api/v1/audio-tools/status",
    "/api/v1/nlp/status",
    "/api/v1/extract-web/status",
    "/api/v1/document/status",
    "/api/v1/embeddings/status",
    "/api/v1/whisperx/status",
    "/api/v1/presidio/status",
    "/api/v1/integrations/feishu/status",
    "/api/v1/integrations/wecom/status",
    "/api/v1/integrations/coze/status",
    "/api/v1/integrations/n8n/status",
    "/api/v1/media/status",
    "/api/v1/gemini-image/status",
]


@pytest.mark.parametrize("path", STATUS_ENDPOINTS)
def test_status_endpoints_return_200(auth_client, path):
    resp = auth_client.get(path)
    assert resp.status_code == 200, f"{path} -> {resp.status_code}: {resp.text}"
    data = resp.json()
    assert isinstance(data, dict)
    assert len(data) > 0


def test_edge_tts_voices(auth_client):
    resp = auth_client.get("/api/v1/edge-tts/voices", params={"locale": "zh-CN"})
    # 需要外网访问微软 TTS 服务；离线时可能 500
    assert resp.status_code in (200, 500)
    if resp.status_code == 200:
        data = resp.json()
        assert "voices" in data
        assert isinstance(data["voices"], list)
