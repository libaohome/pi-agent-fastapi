import tempfile
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile

from app.core.auth import AuthContext, get_current_user
from app.schemas.common import WhisperResponse
from app.services.whisper_service import transcribe_audio

router = APIRouter(prefix="/whisper", tags=["whisper"])


@router.post("/transcribe", response_model=WhisperResponse)
async def transcribe(
    file: Annotated[UploadFile, File(...)],
    _: Annotated[AuthContext, Depends(get_current_user)],
    language: Annotated[str | None, Query(description="ISO-639-1 语言代码，留空自动检测")] = None,
) -> WhisperResponse:
    suffix = Path(file.filename or "audio.wav").suffix or ".wav"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = Path(tmp.name)
    try:
        result = transcribe_audio(tmp_path, language=language)
    except Exception as exc:
        raise HTTPException(500, detail=f"转写失败: {exc}") from exc
    finally:
        tmp_path.unlink(missing_ok=True)
    return WhisperResponse(**result)
