import httpx

from app.config import get_settings


class FeishuClient:
    def __init__(self) -> None:
        settings = get_settings()
        self.app_id = settings.feishu_app_id
        self.app_secret = settings.feishu_app_secret
        self._tenant_token: str | None = None

    @property
    def configured(self) -> bool:
        return bool(self.app_id and self.app_secret)

    async def get_tenant_access_token(self) -> str:
        if not self.configured:
            raise RuntimeError("飞书未配置 FEISHU_APP_ID / FEISHU_APP_SECRET")
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
                json={"app_id": self.app_id, "app_secret": self.app_secret},
            )
            resp.raise_for_status()
            data = resp.json()
            if data.get("code") != 0:
                raise RuntimeError(data.get("msg", "获取飞书 token 失败"))
            return data["tenant_access_token"]

    async def send_text_message(self, receive_id: str, text: str, receive_id_type: str = "open_id") -> dict:
        token = await self.get_tenant_access_token()
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://open.feishu.cn/open-apis/im/v1/messages",
                params={"receive_id_type": receive_id_type},
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "receive_id": receive_id,
                    "msg_type": "text",
                    "content": {"text": text},
                },
            )
            resp.raise_for_status()
            return resp.json()
