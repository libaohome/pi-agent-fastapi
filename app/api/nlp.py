from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import AuthContext, get_current_user
from app.schemas.common import NlpSegmentRequest, NlpSegmentResponse
from app.services import nlp_service as nlp

router = APIRouter(prefix="/nlp", tags=["nlp"])


@router.get("/status")
async def nlp_status(_: Annotated[AuthContext, Depends(get_current_user)]):
    return nlp.status()


@router.post("/segment", response_model=NlpSegmentResponse)
async def segment_text(
    body: NlpSegmentRequest,
    _: Annotated[AuthContext, Depends(get_current_user)],
):
    try:
        result = await nlp.segment_async(
            body.text,
            engine=body.engine,
            cut_all=body.cut_all,
            use_hmm=body.use_hmm,
            extract_keywords=body.extract_keywords,
            top_k=body.top_k,
            model_name=body.model_name,
            postag=body.postag,
        )
    except RuntimeError as exc:
        raise HTTPException(503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(500, detail=f"分词失败: {exc}") from exc
    return NlpSegmentResponse(**result)
