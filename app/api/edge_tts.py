import base64
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response, StreamingResponse

from app.core.auth import AuthContext, get_current_user
from app.schemas.common import EdgeTtsSynthesizeRequest, EdgeTtsSynthesizeResponse, EdgeTtsVoicesResponse
from app.services.edge_tts_service import (
    SynthesisError,
    resolve_voice,
    list_voices,
    synthesize_stream,
    synthesize_to_bytes,
)

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


@router.post(
    "/synthesize",
    responses={
        200: {
            "description": "默认返回 MP3 二进制；`return_base64=true` 时返回 JSON",
            "content": {
                "audio/mpeg": {"schema": {"type": "string", "format": "binary"}},
                "application/json": {"schema": {"$ref": "#/components/schemas/EdgeTtsSynthesizeResponse"}},
            },
        }
    },
)
async def synthesize(
    body: EdgeTtsSynthesizeRequest,
    _: Annotated[AuthContext, Depends(get_current_user)],
):
    if body.return_base64 and body.stream:
        raise HTTPException(400, detail="return_base64 与 stream 不能同时为 true")

    voice = resolve_voice(body.voice)
    try:
        if body.return_base64:
            audio = await synthesize_to_bytes(
                body.text,
                body.voice,
                body.rate,
                body.volume,
                body.pitch,
            )
            return EdgeTtsSynthesizeResponse(
                audio_base64=base64.b64encode(audio).decode(),
                size_bytes=len(audio),
                voice=voice,
            )

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
                headers={"Content-Disposition": 'attachment; filename="speech.mp3"'},
            )

        audio = await synthesize_to_bytes(
            body.text,
            body.voice,
            body.rate,
            body.volume,
            body.pitch,
        )
    except SynthesisError as exc:
        raise HTTPException(502, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(500, detail=f"语音合成失败: {exc}") from exc

    return Response(
        content=audio,
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": 'attachment; filename="speech.mp3"',
            "Content-Length": str(len(audio)),
        },
    )
