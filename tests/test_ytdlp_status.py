from app.services import ffmpeg_service, ytdlp_service


def test_ytdlp_status_has_version():
    status = ytdlp_service.status()
    assert "ytdlp_version" in status
    assert "ffmpeg_available" in status


def test_ffmpeg_status_structure():
    status = ffmpeg_service.status()
    assert "ffmpeg_available" in status
    assert "ffprobe_available" in status
