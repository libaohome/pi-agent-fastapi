import asyncio
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.config import get_settings
from app.services._lazy import try_import


@lru_cache
def _get_ocr():
    paddleocr = try_import("paddleocr")
    if paddleocr is None:
        raise RuntimeError("PaddleOCR 未安装，请执行: pip install -e \".[ml]\"")
    settings = get_settings()
    return paddleocr.PaddleOCR(
        use_angle_cls=settings.paddleocr_use_angle_cls,
        lang=settings.paddleocr_lang,
        show_log=False,
    )


def status() -> dict[str, Any]:
    available = try_import("paddleocr") is not None
    settings = get_settings()
    return {
        "available": available,
        "lang": settings.paddleocr_lang,
        "use_angle_cls": settings.paddleocr_use_angle_cls,
    }


def _serialize_result(raw: list) -> list[dict[str, Any]]:
    lines: list[dict[str, Any]] = []
    for block in raw or []:
        if not block:
            continue
        for item in block:
            box, text_score = item
            text, score = text_score
            lines.append(
                {
                    "text": text,
                    "confidence": float(score),
                    "box": [[float(x), float(y)] for x, y in box],
                }
            )
    return lines


def recognize_image(file_path: Path) -> dict[str, Any]:
    ocr = _get_ocr()
    result = ocr.ocr(str(file_path), cls=get_settings().paddleocr_use_angle_cls)
    lines = _serialize_result(result)
    return {
        "text": "\n".join(line["text"] for line in lines),
        "lines": lines,
        "line_count": len(lines),
    }


async def recognize_image_async(file_path: Path) -> dict[str, Any]:
    return await asyncio.to_thread(recognize_image, file_path)
