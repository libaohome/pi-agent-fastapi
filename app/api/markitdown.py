import tempfile
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.core.auth import AuthContext, get_current_user
from app.schemas.common import MarkItDownResponse, MarkItDownUrlRequest
from app.services.markitdown_service import (
    convert_file_to_markdown,
    convert_url_to_markdown,
    download_and_convert,
)

router = APIRouter(prefix="/markitdown", tags=["markitdown"])


@router.post("/convert/file", response_model=MarkItDownResponse)
async def convert_file(
    file: Annotated[UploadFile, File(...)],
    _: Annotated[AuthContext, Depends(get_current_user)],
) -> MarkItDownResponse:
    suffix = Path(file.filename or "upload.bin").suffix
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = Path(tmp.name)
    try:
        markdown = convert_file_to_markdown(tmp_path)
    except Exception as exc:
        raise HTTPException(400, detail=f"转换失败: {exc}") from exc
    finally:
        tmp_path.unlink(missing_ok=True)
    return MarkItDownResponse(markdown=markdown, source=file.filename or "upload")


@router.post("/convert/url", response_model=MarkItDownResponse)
async def convert_url(
    body: MarkItDownUrlRequest,
    _: Annotated[AuthContext, Depends(get_current_user)],
) -> MarkItDownResponse:
    url = str(body.url)
    try:
        markdown = convert_url_to_markdown(url)
    except Exception:
        try:
            markdown = await download_and_convert(url)
        except Exception as exc:
            raise HTTPException(400, detail=f"URL 转换失败: {exc}") from exc
    return MarkItDownResponse(markdown=markdown, source=url)
