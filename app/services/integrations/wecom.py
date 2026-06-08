import httpx

from app.config import get_settings


class WeComClient:
    def __init__(self) -> None:
        settings = get_settings()
        self.corp_id = settings.wecom_corp_id
        self.agent_id = settings.wecom_agent_id
        self.secret = settings.wecom_secret

    @property
    def configured(self) -> bool:
        return bool(self.corp_id and self.agent_id and self.secret)

    async def get_access_token(self) -> str:
        if not self.configured:
            raise RuntimeError("企微未配置 WECOM_CORP_ID / WECOM_AGENT_ID / WECOM_SECRET")
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                "https://qyapi.weixin.qq.com/cgi-bin/gettoken",
                params={"corpid": self.corp_id, "corpsecret": self.secret},
            )
            resp.raise_for_status()
            data = resp.json()
            if data.get("errcode", 0) != 0:
                raise RuntimeError(data.get("errmsg", "获取企微 token 失败"))
            return data["access_token"]

    async def send_text_message(self, user_id: str, content: str) -> dict:
        token = await self.get_access_token()
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://qyapi.weixin.qq.com/cgi-bin/message/send",
                params={"access_token": token},
                json={
                    "touser": user_id,
                    "msgtype": "text",
                    "agentid": self.agent_id,
                    "text": {"content": content},
                },
            )
            resp.raise_for_status()
            return resp.json()
