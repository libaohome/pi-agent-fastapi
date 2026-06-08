from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import AuthContext, get_current_user
from app.schemas.common import FeishuMessageRequest
from app.services.integrations.feishu import FeishuClient

router = APIRouter(prefix="/integrations/feishu", tags=["integrations-feishu"])


@router.get("/status")
async def feishu_status(_: Annotated[AuthContext, Depends(get_current_user)]):
    client = FeishuClient()
    return {"configured": client.configured}


@router.post("/messages/text")
async def send_feishu_text(
    body: FeishuMessageRequest,
    _: Annotated[AuthContext, Depends(get_current_user)],
):
    client = FeishuClient()
    try:
        result = await client.send_text_message(
            body.receive_id, body.text, body.receive_id_type
        )
    except RuntimeError as exc:
        raise HTTPException(503, detail=str(exc)) from exc
    return result
