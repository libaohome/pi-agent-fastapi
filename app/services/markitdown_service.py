import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import httpx
from markitdown import MarkItDown

from app.services.playwright_sandbox import validate_target_url

_md = MarkItDown()
_DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

ContentFormat = Literal["markdown", "text"]


@dataclass(frozen=True)
class ConvertResult:
    content: str
    method: str
    format: ContentFormat


class UrlConvertError(RuntimeError):
    pass


def _markitdown_result(file_path: Path) -> ConvertResult:
    result = _md.convert(str(file_path))
    markdown = (result.markdown or result.text_content or "").strip()
    if not markdown:
        return ConvertResult(content="", method="markitdown", format="text")
    return ConvertResult(content=markdown, method="markitdown", format="markdown")


def convert_file_to_markdown(file_path: Path) -> str:
    return _markitdown_result(file_path).content


def convert_file(file_path: Path) -> ConvertResult:
    result = _markitdown_result(file_path)
    if not result.content.strip():
        raise UrlConvertError("未能从文件中提取到文本内容")
    return result


def convert_url_to_markdown(url: str) -> str:
    validate_target_url(url)
    result = _md.convert(url)
    return (result.markdown or result.text_content or "").strip()


def _convert_html_bytes(content: bytes, suffix: str = ".html") -> ConvertResult:
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)
    try:
        converted = _markitdown_result(tmp_path)
        if converted.content:
            return ConvertResult(
                content=converted.content,
                method="markitdown_download",
                format="markdown",
            )
        return ConvertResult(content="", method="markitdown_download", format="text")
    finally:
        tmp_path.unlink(missing_ok=True)


async def download_html_async(url: str, timeout: int = 60) -> str:
    validate_target_url(url)
    async with httpx.AsyncClient(follow_redirects=True, timeout=timeout, headers=_DEFAULT_HEADERS) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.text


async def download_and_convert(url: str) -> ConvertResult:
    html = await download_html_async(url)
    return _convert_html_bytes(html.encode("utf-8", errors="ignore"), ".html")
