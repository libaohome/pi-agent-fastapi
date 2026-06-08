import tempfile
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.core.auth import AuthContext, get_current_user
from app.services import ffmpeg_service as ff

router = APIRouter(prefix="/ffmpeg", tags=["ffmpeg"])


@router.get("/status")
async def ffmpeg_status(_: Annotated[AuthContext, Depends(get_current_user)]):
    return ff.status()


@router.post("/probe")
async def probe_file(
    file: Annotated[UploadFile, File(...)],
    _: Annotated[AuthContext, Depends(get_current_user)],
):
    suffix = Path(file.filename or "media.bin").suffix
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = Path(tmp.name)
    try:
        info = await ff.probe_media_async(tmp_path)
    except ff.FfmpegError as exc:
        raise HTTPException(503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(500, detail=f"探测失败: {exc}") from exc
    finally:
        tmp_path.unlink(missing_ok=True)
    return {"probe": info}


@router.post("/transcode")
async def transcode_file(
    file: Annotated[UploadFile, File(...)],
    _: Annotated[AuthContext, Depends(get_current_user)],
    output_format: Annotated[str, Form()] = "mp4",
    video_codec: Annotated[str, Form()] = "libx264",
    audio_codec: Annotated[str, Form()] = "aac",
    crf: Annotated[int, Form(ge=0, le=51)] = 23,
):
    if not ff.ffmpeg_path():
        raise HTTPException(503, detail="ffmpeg 未安装，请先安装系统 ffmpeg")

    suffix = Path(file.filename or "input.bin").suffix
    with tempfile.TemporaryDirectory() as tmp_dir:
        input_path = Path(tmp_dir) / f"input{suffix}"
        output_path = Path(tmp_dir) / "output"
        input_path.write_bytes(await file.read())
        try:
            out = await ff.transcode_async(
                input_path,
                output_path,
                output_format=output_format,
                video_codec=video_codec,
                audio_codec=audio_codec,
                crf=crf,
            )
        except ff.FfmpegError as exc:
            raise HTTPException(500, detail=str(exc)) from exc
        return FileResponse(path=out, filename=f"transcoded.{output_format}")


@router.post("/extract-audio")
async def extract_audio(
    file: Annotated[UploadFile, File(...)],
    _: Annotated[AuthContext, Depends(get_current_user)],
    audio_format: Annotated[str, Form()] = "mp3",
    audio_bitrate: Annotated[str, Form()] = "192k",
):
    if not ff.ffmpeg_path():
        raise HTTPException(503, detail="ffmpeg 未安装，请先安装系统 ffmpeg")

    suffix = Path(file.filename or "input.bin").suffix
    with tempfile.TemporaryDirectory() as tmp_dir:
        input_path = Path(tmp_dir) / f"input{suffix}"
        output_path = Path(tmp_dir) / "audio"
        input_path.write_bytes(await file.read())
        try:
            out = await ff.extract_audio_async(
                input_path,
                output_path,
                audio_format=audio_format,
                audio_bitrate=audio_bitrate,
            )
        except ff.FfmpegError as exc:
            raise HTTPException(500, detail=str(exc)) from exc
        return FileResponse(path=out, filename=f"audio.{audio_format}")
