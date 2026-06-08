import httpx

from app.config import get_settings


class MediaGenerationService:
    def __init__(self) -> None:
        settings = get_settings()
        self.base_url = (settings.media_openai_base_url or "").rstrip("/")
        self.api_key = settings.media_openai_api_key
        self.default_image_model = settings.default_image_model
        self.default_video_model = settings.default_video_model

    @property
    def configured(self) -> bool:
        return bool(self.base_url and self.api_key)

    def _headers(self) -> dict[str, str]:
        if not self.configured:
            raise RuntimeError("媒体生成未配置 MEDIA_OPENAI_BASE_URL / MEDIA_OPENAI_API_KEY")
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def generate_image(
        self,
        prompt: str,
        model: str | None = None,
        size: str = "1024x1024",
        n: int = 1,
    ) -> dict:
        async with httpx.AsyncClient(timeout=180) as client:
            resp = await client.post(
                f"{self.base_url}/images/generations",
                headers=self._headers(),
                json={
                    "model": model or self.default_image_model,
                    "prompt": prompt,
                    "size": size,
                    "n": n,
                },
            )
            resp.raise_for_status()
            return resp.json()

    async def generate_video(
        self,
        prompt: str,
        model: str | None = None,
        duration: int = 5,
    ) -> dict:
        """调用 OpenAI 兼容的视频生成端点（部分网关扩展 /videos/generations）。"""
        async with httpx.AsyncClient(timeout=300) as client:
            resp = await client.post(
                f"{self.base_url}/videos/generations",
                headers=self._headers(),
                json={
                    "model": model or self.default_video_model,
                    "prompt": prompt,
                    "duration": duration,
                },
            )
            resp.raise_for_status()
            return resp.json()
