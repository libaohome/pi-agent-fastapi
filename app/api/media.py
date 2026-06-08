from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import AuthContext, get_current_user
from app.schemas.common import ImageGenerationRequest, VideoGenerationRequest
from app.services.media_generation import MediaGenerationService

router = APIRouter(prefix="/media", tags=["media"])


@router.get("/status")
async def media_status(_: Annotated[AuthContext, Depends(get_current_user)]):
    svc = MediaGenerationService()
    return {"configured": svc.configured}


@router.post("/image/generate")
async def generate_image(
    body: ImageGenerationRequest,
    _: Annotated[AuthContext, Depends(get_current_user)],
):
    svc = MediaGenerationService()
    try:
        result = await svc.generate_image(body.prompt, body.model, body.size, body.n)
    except RuntimeError as exc:
        raise HTTPException(503, detail=str(exc)) from exc
    return result


@router.post("/video/generate")
async def generate_video(
    body: VideoGenerationRequest,
    _: Annotated[AuthContext, Depends(get_current_user)],
):
    svc = MediaGenerationService()
    try:
        result = await svc.generate_video(body.prompt, body.model, body.duration)
    except RuntimeError as exc:
        raise HTTPException(503, detail=str(exc)) from exc
    return result
