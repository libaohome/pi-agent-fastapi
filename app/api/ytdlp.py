import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse

from app.core.auth import AuthContext, get_current_user
from app.schemas.common import (
    YtdlpDownloadRequest,
    YtdlpInfoRequest,
    YtdlpTaskResponse,
    YtdlpTaskSubmitRequest,
)
from app.services import ytdlp_service as ytdlp
from app.services.playwright_sandbox import SandboxError

router = APIRouter(prefix="/ytdlp", tags=["ytdlp"])


@router.get("/status")
async def ytdlp_status(_: Annotated[AuthContext, Depends(get_current_user)]):
    return ytdlp.status()


@router.post("/info")
async def video_info(
    body: YtdlpInfoRequest,
    _: Annotated[AuthContext, Depends(get_current_user)],
):
    try:
        info = await asyncio.to_thread(ytdlp.get_video_info, body.url)
    except SandboxError as exc:
        raise HTTPException(400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(500, detail=f"获取视频信息失败: {exc}") from exc
    return {"info": info}


@router.post("/download")
async def download_video(
    body: YtdlpDownloadRequest,
    user: Annotated[AuthContext, Depends(get_current_user)],
):
    try:
        result = await asyncio.to_thread(ytdlp.download_video, user.user_id, body)
    except SandboxError as exc:
        raise HTTPException(400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(500, detail=f"下载失败: {exc}") from exc
    return result


@router.post("/tasks", response_model=YtdlpTaskResponse)
async def submit_task(
    body: YtdlpTaskSubmitRequest,
    user: Annotated[AuthContext, Depends(get_current_user)],
):
    try:
        YtdlpDownloadRequest(**body.payload)
        task_id = ytdlp.submit_background_task(user.user_id, body.payload)
    except (SandboxError, ValueError) as exc:
        raise HTTPException(400, detail=str(exc)) from exc
    return YtdlpTaskResponse(task_id=task_id, status="pending")


@router.get("/tasks/{task_id}", response_model=YtdlpTaskResponse)
async def get_task(
    task_id: str,
    user: Annotated[AuthContext, Depends(get_current_user)],
):
    task = ytdlp.get_task(task_id, user.user_id)
    if not task:
        raise HTTPException(404, detail="任务不存在")
    return YtdlpTaskResponse(
        task_id=task["id"],
        status=task["status"],
        result=task.get("result"),
        error=task.get("error"),
        created_at=task.get("created_at"),
        completed_at=task.get("completed_at"),
    )


@router.get("/tasks/{task_id}/file")
async def download_task_file(
    task_id: str,
    user: Annotated[AuthContext, Depends(get_current_user)],
    filename: Annotated[str | None, Query(description="多文件时指定文件名")] = None,
):
    file_path = ytdlp.resolve_task_file(task_id, user.user_id, filename)
    if not file_path or not file_path.exists():
        raise HTTPException(404, detail="文件不存在或任务未完成")
    return FileResponse(path=file_path, filename=file_path.name)
