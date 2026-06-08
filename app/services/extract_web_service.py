import asyncio
from typing import Any

import httpx

from app.services._lazy import try_import
from app.services.playwright_sandbox import SandboxError, validate_target_url


def status() -> dict[str, Any]:
    return {"available": try_import("trafilatura") is not None}


def extract_from_html(html: str, url: str | None = None, favor_precision: bool = True) -> dict[str, Any]:
    trafilatura = try_import("trafilatura")
    if trafilatura is None:
        raise RuntimeError("trafilatura 未安装，请执行: pip install -e \".[ml,top5]\"")
    text = trafilatura.extract(
        html,
        url=url,
        include_comments=False,
        include_tables=True,
        favor_precision=favor_precision,
        output_format="txt",
    )
    metadata = trafilatura.extract_metadata(html, default_url=url)
    meta_dict = metadata.as_dict() if metadata else {}
    return {
        "text": text or "",
        "title": meta_dict.get("title"),
        "author": meta_dict.get("author"),
        "url": meta_dict.get("url") or url,
        "date": meta_dict.get("date"),
        "description": meta_dict.get("description"),
        "sitename": meta_dict.get("sitename"),
        "language": meta_dict.get("language"),
    }


def extract_from_url(url: str, favor_precision: bool = True, timeout: int = 30) -> dict[str, Any]:
    trafilatura = try_import("trafilatura")
    if trafilatura is None:
        raise RuntimeError("trafilatura 未安装，请执行: pip install -e \".[ml,top5]\"")
    target = validate_target_url(url)
    downloaded = trafilatura.fetch_url(target)
    if not downloaded:
        with httpx.Client(follow_redirects=True, timeout=timeout) as client:
            resp = client.get(target)
            resp.raise_for_status()
            downloaded = resp.text
    return extract_from_html(downloaded, url=target, favor_precision=favor_precision)


async def extract_from_url_async(url: str, **kwargs: Any) -> dict[str, Any]:
    return await asyncio.to_thread(extract_from_url, url, **kwargs)


async def extract_from_html_async(html: str, **kwargs: Any) -> dict[str, Any]:
    return await asyncio.to_thread(extract_from_html, html, **kwargs)
