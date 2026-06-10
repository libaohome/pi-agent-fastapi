from app.main import app


def test_openapi_has_bearer_security():
    schema = app.openapi()
    assert "BearerAuth" in schema["components"]["securitySchemes"]
    assert schema["components"]["securitySchemes"]["BearerAuth"]["scheme"] == "bearer"


def test_openapi_tags_grouped():
    schema = app.openapi()
    tag_names = {t["name"] for t in schema["tags"]}
    assert "ocr" in tag_names
    assert "pdf" in tag_names
    assert "nlp" in tag_names
    assert "gemini-image" in tag_names

    groups = schema.get("x-tagGroups", [])
    assert groups, "应配置 x-tagGroups 以便 Swagger UI 分组展示"
    grouped_tags = {tag for group in groups for tag in group["tags"]}
    assert grouped_tags >= {
        "markitdown",
        "pdf",
        "ocr",
        "document",
        "extract-web",
        "image",
        "whisper",
        "whisperx",
        "edge-tts",
        "audio-tools",
        "embeddings",
        "presidio",
        "ytdlp",
        "ffmpeg",
        "video-tools",
        "langextract",
        "nlp",
        "knowledge-graph",
        "media",
        "gemini-image",
        "playwright",
        "integrations-feishu",
        "integrations-wecom",
        "integrations-coze",
        "integrations-n8n",
        "system",
    }


def test_api_paths_require_auth():
    schema = app.openapi()
    ocr_path = schema["paths"].get("/api/v1/ocr/recognize", {})
    post = ocr_path.get("post", {})
    assert post.get("security") == [{"BearerAuth": []}]


def test_health_is_public():
    schema = app.openapi()
    health = schema["paths"].get("/health", {}).get("get", {})
    assert "security" not in health
