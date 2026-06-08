from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response

from app.api._upload import save_upload
from app.core.auth import AuthContext, get_current_user
from app.services import rembg_service as rembg

router = APIRouter(prefix="/image", tags=["image"])


@router.get("/status")
async def image_status(_: Annotated[AuthContext, Depends(get_current_user)]):
    return {"rembg": rembg.status()}


@router.post("/remove-background")
async def remove_background(
    file: Annotated[UploadFile, File(...)],
    _: Annotated[AuthContext, Depends(get_current_user)],
):
    image_bytes = await file.read()
    try:
        output = await rembg.remove_background_async(image_bytes)
    except RuntimeError as exc:
        raise HTTPException(503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(500, detail=f"抠图失败: {exc}") from exc
    return Response(content=output, media_type="image/png")
