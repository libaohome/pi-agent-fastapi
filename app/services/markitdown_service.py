import tempfile
from pathlib import Path
from urllib.parse import urlparse

import httpx
from markitdown import MarkItDown

_md = MarkItDown()


def convert_file_to_markdown(file_path: Path) -> str:
    result = _md.convert(str(file_path))
    return result.text_content or ""


def convert_url_to_markdown(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("仅支持 http/https URL")
    result = _md.convert(url)
    return result.text_content or ""


async def download_and_convert(url: str) -> str:
    async with httpx.AsyncClient(follow_redirects=True, timeout=60) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        suffix = Path(urlparse(url).path).suffix or ".bin"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(resp.content)
            tmp_path = Path(tmp.name)
    try:
        return convert_file_to_markdown(tmp_path)
    finally:
        tmp_path.unlink(missing_ok=True)
