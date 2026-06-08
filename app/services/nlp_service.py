import asyncio
from typing import Any, Literal

from app.services._lazy import try_import


def status() -> dict[str, Any]:
    import sys

    pkuseg_available = try_import("pkuseg") is not None
    return {
        "jieba": try_import("jieba") is not None,
        "pkuseg": pkuseg_available,
        "pkuseg_supported": sys.version_info < (3, 12),
        "pkuseg_note": "pkuseg 不支持 Python 3.12+，请使用 jieba" if sys.version_info >= (3, 12) else None,
    }


def segment_jieba(
    text: str,
    *,
    cut_all: bool = False,
    use_hmm: bool = True,
    extract_keywords: bool = False,
    top_k: int = 10,
) -> dict[str, Any]:
    jieba = try_import("jieba")
    if jieba is None:
        raise RuntimeError("jieba 未安装，请执行: pip install -e \".[ml]\"")
    words = jieba.lcut(text, cut_all=cut_all, HMM=use_hmm)
    result: dict[str, Any] = {"engine": "jieba", "words": words, "word_count": len(words)}
    if extract_keywords:
        import jieba.analyse

        tags = jieba.analyse.extract_tags(text, topK=top_k, withWeight=True)
        result["keywords"] = [{"word": w, "weight": float(weight)} for w, weight in tags]
    return result


def segment_pkuseg(
    text: str,
    *,
    model_name: str = "default",
    postag: bool = False,
) -> dict[str, Any]:
    import sys

    if sys.version_info >= (3, 12):
        raise RuntimeError("pkuseg 不支持 Python 3.12+，请使用 engine=jieba")
    pkuseg = try_import("pkuseg")
    if pkuseg is None:
        raise RuntimeError("pkuseg 未安装（仅支持 Python 3.10/3.11）")
    seg = pkuseg.pkuseg(model_name=model_name, postag=postag)
    if postag:
        pairs = seg.cut(text)
        return {
            "engine": "pkuseg",
            "tokens": [{"word": w, "pos": p} for w, p in pairs],
            "word_count": len(pairs),
        }
    words = seg.cut(text)
    return {"engine": "pkuseg", "words": list(words), "word_count": len(words)}


def segment(
    text: str,
    engine: Literal["jieba", "pkuseg"] = "jieba",
    **kwargs: Any,
) -> dict[str, Any]:
    if engine == "pkuseg":
        return segment_pkuseg(text, **kwargs)
    return segment_jieba(text, **kwargs)


async def segment_async(text: str, engine: Literal["jieba", "pkuseg"] = "jieba", **kwargs: Any) -> dict[str, Any]:
    if engine == "pkuseg":
        allowed = {k: kwargs[k] for k in ("model_name", "postag") if k in kwargs}
        return await asyncio.to_thread(segment_pkuseg, text, **allowed)
    allowed = {k: kwargs[k] for k in ("cut_all", "use_hmm", "extract_keywords", "top_k") if k in kwargs}
    return await asyncio.to_thread(segment_jieba, text, **allowed)
