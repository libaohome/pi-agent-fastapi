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


def test_api_paths_require_auth():
    schema = app.openapi()
    ocr_path = schema["paths"].get("/api/v1/ocr/recognize", {})
    post = ocr_path.get("post", {})
    assert post.get("security") == [{"BearerAuth": []}]


def test_health_is_public():
    schema = app.openapi()
    health = schema["paths"].get("/health", {}).get("get", {})
    assert "security" not in health
