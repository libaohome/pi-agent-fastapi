from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import AuthContext, get_current_user
from app.schemas.common import ExtractWebHtmlRequest, ExtractWebUrlRequest, ExtractWebResponse
from app.services import extract_web_service as web
from app.services.playwright_sandbox import SandboxError

router = APIRouter(prefix="/extract-web", tags=["extract-web"])


@router.get("/status")
async def extract_web_status(_: Annotated[AuthContext, Depends(get_current_user)]):
    return web.status()


@router.post("/url", response_model=ExtractWebResponse)
async def extract_url(
    body: ExtractWebUrlRequest,
    _: Annotated[AuthContext, Depends(get_current_user)],
):
    try:
        result = await web.extract_from_url_async(body.url, favor_precision=body.favor_precision)
    except SandboxError as exc:
        raise HTTPException(400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(500, detail=f"正文抽取失败: {exc}") from exc
    return ExtractWebResponse(**result)


@router.post("/html", response_model=ExtractWebResponse)
async def extract_html(
    body: ExtractWebHtmlRequest,
    _: Annotated[AuthContext, Depends(get_current_user)],
):
    try:
        result = await web.extract_from_html_async(
            body.html, url=body.url, favor_precision=body.favor_precision
        )
    except RuntimeError as exc:
        raise HTTPException(503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(500, detail=f"正文抽取失败: {exc}") from exc
    return ExtractWebResponse(**result)
