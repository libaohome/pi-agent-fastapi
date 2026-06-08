from app.services import (
    document_service,
    embeddings_service,
    extract_web_service,
    presidio_service,
    whisperx_service,
)


def test_top5_status_endpoints():
    assert "available" in extract_web_service.status()
    assert "available" in document_service.status()
    assert "model" in embeddings_service.status()
    assert "model" in whisperx_service.status()
    assert "default_language" in presidio_service.status()
