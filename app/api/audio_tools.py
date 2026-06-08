import tempfile
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.api._upload import save_upload
from app.core.auth import AuthContext, get_current_user
from app.services import audio_process_service as audio

router = APIRouter(prefix="/audio-tools", tags=["audio-tools"])


@router.get("/status")
async def audio_status(_: Annotated[AuthContext, Depends(get_current_user)]):
    return audio.status()


@router.post("/librosa/analyze")
async def analyze_audio(
    file: Annotated[UploadFile, File(...)],
    _: Annotated[AuthContext, Depends(get_current_user)],
):
    tmp_path = await save_upload(file)
    try:
        result = await audio.analyze_librosa_async(tmp_path)
    except RuntimeError as exc:
        raise HTTPException(503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(500, detail=f"音频分析失败: {exc}") from exc
    finally:
        tmp_path.unlink(missing_ok=True)
    return result


@router.post("/pydub/slice")
async def slice_audio(
    file: Annotated[UploadFile, File(...)],
    _: Annotated[AuthContext, Depends(get_current_user)],
    start_ms: Annotated[int, Form(ge=0)] = 0,
    end_ms: Annotated[int, Form(gt=0)] = 10000,
    fmt: Annotated[str, Form()] = "mp3",
):
    tmp_path = await save_upload(file)
    with tempfile.TemporaryDirectory() as tmp_dir:
        out = Path(tmp_dir) / f"slice.{fmt}"
        try:
            result = await audio.slice_pydub_async(tmp_path, start_ms, end_ms, out, fmt=fmt)
        except RuntimeError as exc:
            raise HTTPException(503, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(500, detail=f"音频切片失败: {exc}") from exc
        finally:
            tmp_path.unlink(missing_ok=True)
        return FileResponse(path=result, filename=result.name)


@router.post("/pydub/convert")
async def convert_audio(
    file: Annotated[UploadFile, File(...)],
    _: Annotated[AuthContext, Depends(get_current_user)],
    fmt: Annotated[str, Form()] = "wav",
    bitrate: Annotated[str, Form()] = "192k",
):
    tmp_path = await save_upload(file)
    with tempfile.TemporaryDirectory() as tmp_dir:
        out = Path(tmp_dir) / f"converted.{fmt}"
        try:
            result = await audio.convert_pydub_async(tmp_path, out, fmt=fmt, bitrate=bitrate)
        except RuntimeError as exc:
            raise HTTPException(503, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(500, detail=f"音频转换失败: {exc}") from exc
        finally:
            tmp_path.unlink(missing_ok=True)
        return FileResponse(path=result, filename=result.name)


@router.post("/demucs/separate")
async def separate_stems(
    file: Annotated[UploadFile, File(...)],
    user: Annotated[AuthContext, Depends(get_current_user)],
    stems: Annotated[str, Form()] = "vocals",
):
    tmp_path = await save_upload(file)
    try:
        result = await audio.separate_demucs_async(tmp_path, user.user_id, stems=stems)
    except RuntimeError as exc:
        raise HTTPException(503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(500, detail=f"音轨分离失败: {exc}") from exc
    finally:
        tmp_path.unlink(missing_ok=True)
    return result
