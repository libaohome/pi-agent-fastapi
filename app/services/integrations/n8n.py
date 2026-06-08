import httpx

from app.config import get_settings


class N8nClient:
    def __init__(self) -> None:
        settings = get_settings()
        self.webhook_base = (settings.n8n_webhook_base or "").rstrip("/")
        self.api_key = settings.n8n_api_key

    @property
    def configured(self) -> bool:
        return bool(self.webhook_base)

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def trigger_webhook(self, workflow_path: str, payload: dict) -> dict:
        if not self.configured:
            raise RuntimeError("n8n 未配置 N8N_WEBHOOK_BASE")
        url = f"{self.webhook_base}/{workflow_path.lstrip('/')}"
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(url, headers=self._headers(), json=payload)
            resp.raise_for_status()
            if resp.content:
                return resp.json()
            return {"ok": True}
