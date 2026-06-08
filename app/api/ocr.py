from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.api._upload import save_upload
from app.core.auth import AuthContext, get_current_user
from app.schemas.common import OcrResponse
from app.services import ocr_service as ocr

router = APIRouter(prefix="/ocr", tags=["ocr"])


@router.get("/status")
async def ocr_status(_: Annotated[AuthContext, Depends(get_current_user)]):
    return ocr.status()


@router.post("/recognize", response_model=OcrResponse)
async def recognize(
    file: Annotated[UploadFile, File(...)],
    _: Annotated[AuthContext, Depends(get_current_user)],
):
    tmp_path = await save_upload(file)
    try:
        result = await ocr.recognize_image_async(tmp_path)
    except RuntimeError as exc:
        raise HTTPException(503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(500, detail=f"OCR 识别失败: {exc}") from exc
    finally:
        tmp_path.unlink(missing_ok=True)
    return OcrResponse(**result)
