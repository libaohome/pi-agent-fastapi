from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse

from app.core.auth import AuthContext, get_current_user
from app.schemas.common import LangExtractRequest, LangExtractResponse, LangExtractVisualizeResponse
from app.services.langextract_service import extract_structured, extract_with_visualization

router = APIRouter(prefix="/langextract", tags=["langextract"])


@router.get("/status")
async def langextract_status(_: Annotated[AuthContext, Depends(get_current_user)]):
    from app.config import get_settings

    settings = get_settings()
    return {
        "default_provider": settings.langextract_default_provider,
        "default_model": settings.langextract_default_model,
        "openai_configured": bool(settings.langextract_openai_api_key),
        "gemini_configured": bool(settings.langextract_api_key),
        "ollama_url": settings.langextract_ollama_url,
    }


@router.post("/extract", response_model=LangExtractResponse)
async def run_extract(
    body: LangExtractRequest,
    _: Annotated[AuthContext, Depends(get_current_user)],
):
    try:
        result = await extract_structured(body)
    except ValueError as exc:
        raise HTTPException(400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(500, detail=f"结构化抽取失败: {exc}") from exc
    return LangExtractResponse(**result)


@router.post("/extract/visualize", response_model=LangExtractVisualizeResponse)
async def run_extract_visualize(
    body: LangExtractRequest,
    _: Annotated[AuthContext, Depends(get_current_user)],
):
    try:
        result, html = await extract_with_visualization(body)
    except ValueError as exc:
        raise HTTPException(400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(500, detail=f"可视化抽取失败: {exc}") from exc
    return LangExtractVisualizeResponse(**result, html=html)


@router.post("/extract/visualize/html", response_class=HTMLResponse)
async def run_extract_visualize_html(
    body: LangExtractRequest,
    _: Annotated[AuthContext, Depends(get_current_user)],
):
    try:
        _, html = await extract_with_visualization(body)
    except ValueError as exc:
        raise HTTPException(400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(500, detail=f"可视化抽取失败: {exc}") from exc
    return HTMLResponse(content=html)
