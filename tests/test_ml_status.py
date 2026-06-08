from app.services import (
    audio_process_service,
    nlp_service,
    ocr_service,
    pdf_service,
    rembg_service,
    video_process_service,
)


def test_ml_status_endpoints_return_available_key():
    assert "available" in ocr_service.status() or "pymupdf" in pdf_service.status()
    assert "rembg" in rembg_service.status() or "available" in rembg_service.status()
    assert "moviepy" in video_process_service.status()
    assert "librosa" in audio_process_service.status()
    assert "jieba" in nlp_service.status()
