import base64
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response

from app.core.auth import AuthContext, get_current_user
from app.schemas.common import (
    PlaywrightPageRequest,
    PlaywrightPageResponse,
    PlaywrightPdfRequest,
    PlaywrightRunRequest,
    PlaywrightScreenshotRequest,
    PlaywrightTaskResponse,
    PlaywrightTaskSubmitRequest,
)
from app.services import playwright_service as pw
from app.services.playwright_sandbox import SandboxError

router = APIRouter(prefix="/playwright", tags=["playwright"])


def _ensure_ready() -> None:
    if not pw.is_ready():
        raise HTTPException(
            503,
            detail="Playwright 未就绪，请执行: playwright install chromium",
        )


@router.get("/status")
async def playwright_status(_: Annotated[AuthContext, Depends(get_current_user)]):
    from app.config import get_settings

    settings = get_settings()
    return {
        "ready": pw.is_ready(),
        "headless": settings.playwright_headless,
        "chromium_sandbox": settings.playwright_chromium_sandbox,
        "max_concurrent": settings.playwright_max_concurrent,
        "block_private_network": settings.playwright_block_private_network,
        "allowed_hosts": settings.playwright_allowed_hosts,
        "sandbox_dir": settings.playwright_sandbox_dir,
    }


@router.post("/page", response_model=PlaywrightPageResponse)
async def fetch_page(
    body: PlaywrightPageRequest,
    user: Annotated[AuthContext, Depends(get_current_user)],
):
    _ensure_ready()
    try:
        result = await pw.fetch_page(user.user_id, body)
    except SandboxError as exc:
        raise HTTPException(400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(500, detail=f"页面抓取失败: {exc}") from exc
    return PlaywrightPageResponse(
        url=result.url,
        title=result.title,
        text=result.text,
        html=result.html,
        links=result.links,
    )


@router.post("/screenshot")
async def screenshot(
    body: PlaywrightScreenshotRequest,
    user: Annotated[AuthContext, Depends(get_current_user)],
):
    _ensure_ready()
    try:
        png = await pw.take_screenshot(
            user.user_id,
            body.url,
            full_page=body.full_page,
            wait_until=body.wait_until,
            timeout_ms=body.timeout_ms,
        )
    except SandboxError as exc:
        raise HTTPException(400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(500, detail=f"截图失败: {exc}") from exc
    if body.return_base64:
        return {"image_base64": base64.b64encode(png).decode()}
    return Response(content=png, media_type="image/png")


@router.post("/pdf")
async def pdf(
    body: PlaywrightPdfRequest,
    user: Annotated[AuthContext, Depends(get_current_user)],
):
    _ensure_ready()
    try:
        pdf_bytes = await pw.export_pdf(
            user.user_id,
            body.url,
            wait_until=body.wait_until,
            timeout_ms=body.timeout_ms,
        )
    except SandboxError as exc:
        raise HTTPException(400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(500, detail=f"PDF 导出失败: {exc}") from exc
    if body.return_base64:
        return {"pdf_base64": base64.b64encode(pdf_bytes).decode()}
    return Response(content=pdf_bytes, media_type="application/pdf")


@router.post("/run")
async def run_actions(
    body: PlaywrightRunRequest,
    user: Annotated[AuthContext, Depends(get_current_user)],
):
    _ensure_ready()
    try:
        result = await pw.run_actions(user.user_id, body)
    except (SandboxError, ValueError) as exc:
        raise HTTPException(400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(500, detail=f"自动化执行失败: {exc}") from exc
    return result


@router.post("/tasks", response_model=PlaywrightTaskResponse)
async def submit_task(
    body: PlaywrightTaskSubmitRequest,
    user: Annotated[AuthContext, Depends(get_current_user)],
):
    """后台沙箱异步任务：立即返回 task_id，客户端轮询结果。"""
    _ensure_ready()
    try:
        if body.type == "page":
            PlaywrightPageRequest(**body.payload)
        elif body.type == "screenshot":
            PlaywrightScreenshotRequest(**body.payload)
        elif body.type == "pdf":
            PlaywrightPdfRequest(**body.payload)
        elif body.type == "run":
            PlaywrightRunRequest(**body.payload)
        else:
            raise ValueError(f"不支持的任务类型: {body.type}")
        task_id = pw.submit_background_task(user.user_id, body.type, body.payload)
    except (SandboxError, ValueError) as exc:
        raise HTTPException(400, detail=str(exc)) from exc
    return PlaywrightTaskResponse(task_id=task_id, status="pending")


@router.get("/tasks/{task_id}", response_model=PlaywrightTaskResponse)
async def get_task(
    task_id: str,
    user: Annotated[AuthContext, Depends(get_current_user)],
):
    task = pw.get_task(task_id, user.user_id)
    if not task:
        raise HTTPException(404, detail="任务不存在")
    return PlaywrightTaskResponse(
        task_id=task["id"],
        status=task["status"],
        result=task.get("result"),
        error=task.get("error"),
        created_at=task.get("created_at"),
        completed_at=task.get("completed_at"),
    )


@router.get("/tasks")
async def list_tasks(
    user: Annotated[AuthContext, Depends(get_current_user)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
):
    return {"tasks": pw.list_tasks(user.user_id, limit)}
