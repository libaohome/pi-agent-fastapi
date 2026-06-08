from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import AuthContext, get_current_user
from app.schemas.common import PresidioAnalyzeRequest, PresidioAnonymizeRequest, PresidioAnalyzeResponse
from app.services import presidio_service as presidio

router = APIRouter(prefix="/presidio", tags=["presidio"])


@router.get("/status")
async def presidio_status(_: Annotated[AuthContext, Depends(get_current_user)]):
    return presidio.status()


@router.post("/analyze", response_model=PresidioAnalyzeResponse)
async def analyze(
    body: PresidioAnalyzeRequest,
    _: Annotated[AuthContext, Depends(get_current_user)],
):
    try:
        result = await presidio.analyze_text_async(body.text, language=body.language)
    except RuntimeError as exc:
        raise HTTPException(503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(500, detail=f"PII 检测失败: {exc}") from exc
    return PresidioAnalyzeResponse(**result)


@router.post("/anonymize")
async def anonymize(
    body: PresidioAnonymizeRequest,
    _: Annotated[AuthContext, Depends(get_current_user)],
):
    try:
        result = await presidio.anonymize_text_async(body.text, language=body.language)
    except RuntimeError as exc:
        raise HTTPException(503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(500, detail=f"PII 脱敏失败: {exc}") from exc
    return result
