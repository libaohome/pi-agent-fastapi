from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response, StreamingResponse

from app.core.auth import AuthContext, get_current_user
from app.schemas.common import EdgeTtsSynthesizeRequest, EdgeTtsVoicesResponse
from app.services.edge_tts_service import list_voices, synthesize_stream, synthesize_to_bytes

router = APIRouter(prefix="/edge-tts", tags=["edge-tts"])


@router.get("/voices", response_model=EdgeTtsVoicesResponse)
async def get_voices(
    _: Annotated[AuthContext, Depends(get_current_user)],
    locale: Annotated[str | None, Query(description="语言区域过滤，如 zh-CN、en-US")] = None,
):
    try:
        voices = await list_voices(locale)
    except Exception as exc:
        raise HTTPException(500, detail=f"获取语音列表失败: {exc}") from exc
    return EdgeTtsVoicesResponse(voices=voices)


@router.post("/synthesize")
async def synthesize(
    body: EdgeTtsSynthesizeRequest,
    _: Annotated[AuthContext, Depends(get_current_user)],
):
    try:
        if body.stream:
            return StreamingResponse(
                synthesize_stream(
                    body.text,
                    body.voice,
                    body.rate,
                    body.volume,
                    body.pitch,
                ),
                media_type="audio/mpeg",
                headers={"Content-Disposition": 'inline; filename="speech.mp3"'},
            )
        audio = await synthesize_to_bytes(
            body.text,
            body.voice,
            body.rate,
            body.volume,
            body.pitch,
        )
    except Exception as exc:
        raise HTTPException(500, detail=f"语音合成失败: {exc}") from exc
    return Response(
        content=audio,
        media_type="audio/mpeg",
        headers={"Content-Disposition": 'inline; filename="speech.mp3"'},
    )
