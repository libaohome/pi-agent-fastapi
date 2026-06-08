from functools import lru_cache
from pathlib import Path

from faster_whisper import WhisperModel

from app.config import get_settings


@lru_cache
def get_whisper_model() -> WhisperModel:
    settings = get_settings()
    return WhisperModel(
        settings.whisper_model_size,
        device=settings.whisper_device,
        compute_type=settings.whisper_compute_type,
    )


def transcribe_audio(file_path: Path, language: str | None = None) -> dict:
    model = get_whisper_model()
    segments, info = model.transcribe(
        str(file_path),
        language=language,
        vad_filter=True,
    )
    text_parts: list[str] = []
    segment_list: list[dict] = []
    for seg in segments:
        text_parts.append(seg.text.strip())
        segment_list.append(
            {
                "start": seg.start,
                "end": seg.end,
                "text": seg.text.strip(),
            }
        )
    return {
        "language": info.language,
        "duration": info.duration,
        "text": " ".join(text_parts).strip(),
        "segments": segment_list,
    }
