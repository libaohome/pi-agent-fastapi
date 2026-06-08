from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import AuthContext, get_current_user
from app.schemas.common import CozeChatRequest, CozeWorkflowRequest
from app.services.integrations.coze import CozeClient

router = APIRouter(prefix="/integrations/coze", tags=["integrations-coze"])


@router.get("/status")
async def coze_status(_: Annotated[AuthContext, Depends(get_current_user)]):
    client = CozeClient()
    return {"configured": client.configured}


@router.post("/chat")
async def coze_chat(
    body: CozeChatRequest,
    user: Annotated[AuthContext, Depends(get_current_user)],
):
    client = CozeClient()
    try:
        result = await client.chat(body.bot_id, user.user_id, body.query, body.stream)
    except RuntimeError as exc:
        raise HTTPException(503, detail=str(exc)) from exc
    return result


@router.post("/workflow/run")
async def coze_workflow(
    body: CozeWorkflowRequest,
    _: Annotated[AuthContext, Depends(get_current_user)],
):
    client = CozeClient()
    try:
        result = await client.run_workflow(body.workflow_id, body.parameters)
    except RuntimeError as exc:
        raise HTTPException(503, detail=str(exc)) from exc
    return result
