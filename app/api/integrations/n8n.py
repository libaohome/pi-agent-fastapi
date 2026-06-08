from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import AuthContext, get_current_user
from app.schemas.common import N8nWebhookRequest
from app.services.integrations.n8n import N8nClient

router = APIRouter(prefix="/integrations/n8n", tags=["integrations-n8n"])


@router.get("/status")
async def n8n_status(_: Annotated[AuthContext, Depends(get_current_user)]):
    client = N8nClient()
    return {"configured": client.configured}


@router.post("/webhook/trigger")
async def trigger_n8n_webhook(
    body: N8nWebhookRequest,
    user: Annotated[AuthContext, Depends(get_current_user)],
):
    client = N8nClient()
    payload = {**body.payload, "pi_user_id": user.user_id}
    try:
        result = await client.trigger_webhook(body.workflow_path, payload)
    except RuntimeError as exc:
        raise HTTPException(503, detail=str(exc)) from exc
    return result
