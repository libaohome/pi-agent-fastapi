import asyncio
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.config import get_settings
from app.services._lazy import try_import


@lru_cache
def _load_model():
    whisperx = try_import("whisperx")
    if whisperx is None:
        raise RuntimeError("whisperx 未安装，请执行: pip install -e \".[ml,top5]\"")
    settings = get_settings()
    return whisperx, whisperx.load_model(
        settings.whisperx_model,
        settings.whisperx_device,
        compute_type=settings.whisperx_compute_type,
    )


def status() -> dict[str, Any]:
    settings = get_settings()
    return {
        "available": try_import("whisperx") is not None,
        "model": settings.whisperx_model,
        "device": settings.whisperx_device,
        "diarization_configured": bool(settings.whisperx_hf_token),
    }


def transcribe(
    file_path: Path,
    language: str | None = None,
    enable_diarization: bool = False,
    min_speakers: int | None = None,
    max_speakers: int | None = None,
) -> dict[str, Any]:
    settings = get_settings()
    whisperx, model = _load_model()

    audio = whisperx.load_audio(str(file_path))
    result = model.transcribe(audio, batch_size=settings.whisperx_batch_size, language=language)

    aligned_segments = result.get("segments", [])
    detected_lang = result.get("language")

    if settings.whisperx_align:
        try:
            align_model, metadata = whisperx.load_align_model(
                language_code=detected_lang or language or "zh",
                device=settings.whisperx_device,
            )
            result = whisperx.align(
                result["segments"],
                align_model,
                metadata,
                audio,
                settings.whisperx_device,
                return_char_alignments=False,
            )
            aligned_segments = result.get("segments", aligned_segments)
        except Exception:
            pass

    speakers: list[dict[str, Any]] = []
    if enable_diarization and settings.whisperx_hf_token:
        try:
            diarize_model = whisperx.DiarizationPipeline(
                use_auth_token=settings.whisperx_hf_token,
                device=settings.whisperx_device,
            )
            diarize_segments = diarize_model(
                audio,
                min_speakers=min_speakers,
                max_speakers=max_speakers,
            )
            result = whisperx.assign_word_speakers(diarize_segments, result)
            aligned_segments = result.get("segments", aligned_segments)
            for seg in aligned_segments:
                if seg.get("speaker"):
                    speakers.append(
                        {
                            "speaker": seg["speaker"],
                            "start": seg.get("start"),
                            "end": seg.get("end"),
                            "text": seg.get("text", ""),
                        }
                    )
        except Exception as exc:
            speakers = [{"error": f"说话人分离失败: {exc}"}]

    text = " ".join(seg.get("text", "").strip() for seg in aligned_segments).strip()
    return {
        "language": detected_lang,
        "text": text,
        "segments": aligned_segments,
        "speakers": speakers,
        "segment_count": len(aligned_segments),
    }


async def transcribe_async(file_path: Path, **kwargs: Any) -> dict[str, Any]:
    return await asyncio.to_thread(transcribe, file_path, **kwargs)
