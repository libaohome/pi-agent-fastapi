from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import AuthContext, get_current_user
from app.schemas.common import WeComMessageRequest
from app.services.integrations.wecom import WeComClient

router = APIRouter(prefix="/integrations/wecom", tags=["integrations-wecom"])


@router.get("/status")
async def wecom_status(_: Annotated[AuthContext, Depends(get_current_user)]):
    client = WeComClient()
    return {"configured": client.configured}


@router.post("/messages/text")
async def send_wecom_text(
    body: WeComMessageRequest,
    _: Annotated[AuthContext, Depends(get_current_user)],
):
    client = WeComClient()
    try:
        result = await client.send_text_message(body.user_id, body.content)
    except RuntimeError as exc:
        raise HTTPException(503, detail=str(exc)) from exc
    return result
