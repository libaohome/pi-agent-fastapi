from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile

from app.api._upload import save_upload
from app.core.auth import AuthContext, get_current_user
from app.schemas.common import WhisperxResponse
from app.services import whisperx_service as wx

router = APIRouter(prefix="/whisperx", tags=["whisperx"])


@router.get("/status")
async def whisperx_status(_: Annotated[AuthContext, Depends(get_current_user)]):
    return wx.status()


@router.post("/transcribe", response_model=WhisperxResponse)
async def transcribe(
    file: Annotated[UploadFile, File(...)],
    _: Annotated[AuthContext, Depends(get_current_user)],
    language: Annotated[str | None, Query()] = None,
    enable_diarization: Annotated[bool, Query()] = False,
    min_speakers: Annotated[int | None, Query(ge=1)] = None,
    max_speakers: Annotated[int | None, Query(ge=1)] = None,
):
    suffix = Path(file.filename or "audio.wav").suffix or ".wav"
    tmp_path = await save_upload(file, suffix)
    try:
        result = await wx.transcribe_async(
            tmp_path,
            language=language,
            enable_diarization=enable_diarization,
            min_speakers=min_speakers,
            max_speakers=max_speakers,
        )
    except RuntimeError as exc:
        raise HTTPException(503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(500, detail=f"转写失败: {exc}") from exc
    finally:
        tmp_path.unlink(missing_ok=True)
    return WhisperxResponse(**result)
