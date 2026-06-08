import asyncio
from typing import Any

from app.services._lazy import try_import


def status() -> dict[str, Any]:
    return {"available": try_import("rembg") is not None}


def remove_background(image_bytes: bytes) -> bytes:
    rembg = try_import("rembg")
    if rembg is None:
        raise RuntimeError("rembg 未安装，请执行: pip install -e \".[ml]\"")
    return rembg.remove(image_bytes)


async def remove_background_async(image_bytes: bytes) -> bytes:
    return await asyncio.to_thread(remove_background, image_bytes)
