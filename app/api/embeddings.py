from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import AuthContext, get_current_user
from app.schemas.common import (
    EmbeddingEncodeRequest,
    EmbeddingEncodeResponse,
    EmbeddingSimilarityRequest,
    EmbeddingSimilarityResponse,
)
from app.services import embeddings_service as emb

router = APIRouter(prefix="/embeddings", tags=["embeddings"])


@router.get("/status")
async def embeddings_status(_: Annotated[AuthContext, Depends(get_current_user)]):
    return emb.status()


@router.post("/encode", response_model=EmbeddingEncodeResponse)
async def encode(
    body: EmbeddingEncodeRequest,
    _: Annotated[AuthContext, Depends(get_current_user)],
):
    try:
        result = await emb.encode_texts_async(body.texts, normalize=body.normalize)
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(503 if isinstance(exc, RuntimeError) else 400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(500, detail=f"向量化失败: {exc}") from exc
    return EmbeddingEncodeResponse(**result)


@router.post("/similarity", response_model=EmbeddingSimilarityResponse)
async def similarity(
    body: EmbeddingSimilarityRequest,
    _: Annotated[AuthContext, Depends(get_current_user)],
):
    try:
        result = await emb.compute_similarity_async(body.text_a, body.text_b)
    except RuntimeError as exc:
        raise HTTPException(503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(500, detail=f"相似度计算失败: {exc}") from exc
    return EmbeddingSimilarityResponse(**result)
