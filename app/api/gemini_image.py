from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from app.config import get_settings
from app.core.auth import AuthContext, get_current_user
from app.schemas.common import GeminiImageGenerateRequest, GeminiImageGenerateResponse
from app.services import gemini_image_service as gemini_image

router = APIRouter(prefix="/gemini-image", tags=["gemini-image"])


@router.get("/status")
async def gemini_image_status(_: Annotated[AuthContext, Depends(get_current_user)]):
    return gemini_image.status()


@router.post("/generate", response_model=GeminiImageGenerateResponse)
async def generate_gemini_image(
    body: GeminiImageGenerateRequest,
    user: Annotated[AuthContext, Depends(get_current_user)],
):
    if not gemini_image.configured():
        raise HTTPException(
            503,
            detail="Gemini 生图未配置，请在 .env 设置 GEMINI_SECURE_1PSID / GEMINI_SECURE_1PSIDTS",
        )
    settings = get_settings()
    try:
        result = await gemini_image.generate_image(
            body.prompt,
            user.user_id,
            force_generate=body.force_generate,
            full_size=body.full_size,
            storage_mode=body.storage_mode,
            api_prefix=settings.api_prefix,
        )
    except RuntimeError as exc:
        raise HTTPException(503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(500, detail=f"Gemini 生图失败: {exc}") from exc

    if result["image_count"] == 0:
        raise HTTPException(
            422,
            detail=result.get("text")
            or "未生成图片，请检查提示词、账号权限或地区是否支持 AI 生图",
        )
    return GeminiImageGenerateResponse(**result)


@router.get("/files/{file_id}")
async def download_gemini_image(
    file_id: str,
    user: Annotated[AuthContext, Depends(get_current_user)],
):
    """下载已存储的生图文件（按用户隔离）。"""
    file_path = gemini_image.resolve_file(user.user_id, file_id)
    if file_path is None or not file_path.exists():
        raise HTTPException(404, detail="文件不存在或无权访问")
    return FileResponse(path=file_path, filename=file_path.name, media_type=None)
