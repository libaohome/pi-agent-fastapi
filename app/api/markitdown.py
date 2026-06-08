import tempfile
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.core.auth import AuthContext, get_current_user
from app.schemas.common import MarkItDownResponse, MarkItDownUrlRequest
from app.services.markitdown_service import (
    UrlConvertError,
    convert_file,
    convert_url_to_markdown,
    download_and_convert,
)

router = APIRouter(prefix="/markitdown", tags=["markitdown"])


@router.post("/convert/file", response_model=MarkItDownResponse)
async def convert_file_endpoint(
    file: Annotated[UploadFile, File(...)],
    _: Annotated[AuthContext, Depends(get_current_user)],
) -> MarkItDownResponse:
    suffix = Path(file.filename or "upload.bin").suffix
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = Path(tmp.name)
    try:
        result = convert_file(tmp_path)
    except UrlConvertError as exc:
        raise HTTPException(422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(400, detail=f"转换失败: {exc}") from exc
    finally:
        tmp_path.unlink(missing_ok=True)
    return MarkItDownResponse(
        markdown=result.content,
        source=file.filename or "upload",
        format=result.format,
        method=result.method,
    )


@router.post("/convert/url", response_model=MarkItDownResponse)
async def convert_url(
    body: MarkItDownUrlRequest,
    _: Annotated[AuthContext, Depends(get_current_user)],
):
    url = str(body.url)
    method = "markitdown"
    try:
        markdown = convert_url_to_markdown(url)
        fmt = "markdown"
    except Exception:
        try:
            result = await download_and_convert(url)
            markdown = result.content
            method = result.method
            fmt = result.format
        except Exception as exc:
            raise HTTPException(400, detail=f"URL 转换失败: {exc}") from exc
    if not markdown.strip():
        raise HTTPException(422, detail="未能从 URL 提取到文本内容")
    return MarkItDownResponse(markdown=markdown, source=url, format=fmt, method=method)
