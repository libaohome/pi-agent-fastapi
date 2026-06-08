import asyncio
from functools import lru_cache
from typing import Any

from app.config import get_settings
from app.services._lazy import try_import


@lru_cache
def _get_model():
    st = try_import("sentence_transformers")
    if st is None:
        raise RuntimeError("sentence-transformers 未安装，请执行: pip install -e \".[ml,top5]\"")
    settings = get_settings()
    return st.SentenceTransformer(settings.embedding_model_name)


def status() -> dict[str, Any]:
    settings = get_settings()
    return {
        "available": try_import("sentence_transformers") is not None,
        "model": settings.embedding_model_name,
    }


def encode_texts(texts: list[str], normalize: bool = True) -> dict[str, Any]:
    if not texts:
        raise ValueError("texts 不能为空")
    model = _get_model()
    vectors = model.encode(texts, normalize_embeddings=normalize)
    return {
        "model": get_settings().embedding_model_name,
        "count": len(texts),
        "dimension": len(vectors[0]),
        "embeddings": [v.tolist() for v in vectors],
    }


def compute_similarity(text_a: str, text_b: str) -> dict[str, Any]:
    model = _get_model()
    vectors = model.encode([text_a, text_b], normalize_embeddings=True)
    similarity = float(vectors[0] @ vectors[1])
    return {
        "model": get_settings().embedding_model_name,
        "similarity": similarity,
    }


async def encode_texts_async(texts: list[str], normalize: bool = True) -> dict[str, Any]:
    return await asyncio.to_thread(encode_texts, texts, normalize)


async def compute_similarity_async(text_a: str, text_b: str) -> dict[str, Any]:
    return await asyncio.to_thread(compute_similarity, text_a, text_b)
