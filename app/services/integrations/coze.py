import httpx

from app.config import get_settings


class CozeClient:
    def __init__(self) -> None:
        settings = get_settings()
        self.api_base = settings.coze_api_base.rstrip("/")
        self.api_token = settings.coze_api_token

    @property
    def configured(self) -> bool:
        return bool(self.api_token)

    def _headers(self) -> dict[str, str]:
        if not self.api_token:
            raise RuntimeError("Coze 未配置 COZE_API_TOKEN")
        return {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }

    async def chat(self, bot_id: str, user_id: str, query: str, stream: bool = False) -> dict:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{self.api_base}/v3/chat",
                headers=self._headers(),
                json={
                    "bot_id": bot_id,
                    "user_id": user_id,
                    "stream": stream,
                    "additional_messages": [
                        {"role": "user", "content": query, "content_type": "text"}
                    ],
                },
            )
            resp.raise_for_status()
            return resp.json()

    async def run_workflow(self, workflow_id: str, parameters: dict) -> dict:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{self.api_base}/v1/workflow/run",
                headers=self._headers(),
                json={"workflow_id": workflow_id, "parameters": parameters},
            )
            resp.raise_for_status()
            return resp.json()
