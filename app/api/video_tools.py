import asyncio
import tempfile
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response

from app.api._upload import save_upload
from app.core.auth import AuthContext, get_current_user
from app.services import video_process_service as video

router = APIRouter(prefix="/video-tools", tags=["video-tools"])


@router.get("/status")
async def video_status(_: Annotated[AuthContext, Depends(get_current_user)]):
    return video.status()


@router.post("/scenes")
async def detect_scenes(
    file: Annotated[UploadFile, File(...)],
    _: Annotated[AuthContext, Depends(get_current_user)],
    threshold: Annotated[float, Form(ge=1, le=100)] = 27.0,
):
    tmp_path = await save_upload(file)
    try:
        result = await video.detect_scenes_async(tmp_path, threshold=threshold)
    except RuntimeError as exc:
        raise HTTPException(503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(500, detail=f"分镜检测失败: {exc}") from exc
    finally:
        tmp_path.unlink(missing_ok=True)
    return result


@router.post("/clip")
async def clip_video(
    file: Annotated[UploadFile, File(...)],
    _: Annotated[AuthContext, Depends(get_current_user)],
    start_sec: Annotated[float, Form(ge=0)] = 0,
    end_sec: Annotated[float, Form(gt=0)] = 10,
):
    tmp_path = await save_upload(file)
    with tempfile.TemporaryDirectory() as tmp_dir:
        out = Path(tmp_dir) / "clip.mp4"
        try:
            result = await video.clip_video_async(tmp_path, start_sec, end_sec, out)
        except RuntimeError as exc:
            raise HTTPException(503, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(500, detail=f"视频裁剪失败: {exc}") from exc
        finally:
            tmp_path.unlink(missing_ok=True)
        return FileResponse(path=result, filename="clip.mp4", media_type="video/mp4")


@router.post("/thumbnail")
async def thumbnail(
    file: Annotated[UploadFile, File(...)],
    _: Annotated[AuthContext, Depends(get_current_user)],
    at_sec: Annotated[float, Form(ge=0)] = 0,
    return_image: Annotated[bool, Form()] = True,
):
    tmp_path = await save_upload(file)
    try:
        if return_image:
            from app.services.video_process_service import extract_thumbnail

            png = await asyncio.to_thread(extract_thumbnail, tmp_path, at_sec)
            return Response(content=png, media_type="image/png")
        b64 = await video.thumbnail_base64_async(tmp_path, at_sec=at_sec)
    except RuntimeError as exc:
        raise HTTPException(503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(500, detail=f"缩略图生成失败: {exc}") from exc
    finally:
        tmp_path.unlink(missing_ok=True)
    return {"image_base64": b64}
