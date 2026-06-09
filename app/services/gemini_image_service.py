import asyncio
import base64
import logging
import mimetypes
import re
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

from app.config import get_settings
from app.services._lazy import try_import

logger = logging.getLogger(__name__)

_client: Any = None
_lock = asyncio.Lock()
_init_lock = asyncio.Lock()
_account_status_name: str | None = None

_FILE_ID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.I,
)


def configured() -> bool:
    settings = get_settings()
    return bool(settings.gemini_secure_1psid and settings.gemini_secure_1psidts)


def is_ready() -> bool:
    return _client is not None and getattr(_client, "_running", False)


def account_status_name() -> str | None:
    return _account_status_name


def _user_dir(user_id: str) -> Path:
    settings = get_settings()
    return Path(settings.gemini_image_dir) / user_id


def resolve_file(user_id: str, file_id: str) -> Path | None:
    if not _FILE_ID_RE.fullmatch(file_id):
        return None
    user_path = _user_dir(user_id)
    if not user_path.is_dir():
        return None
    for path in user_path.glob(f"{file_id}.*"):
        if path.is_file():
            return path.resolve()
    return None


def _save_image_bytes(user_id: str, data: bytes, content_type: str) -> tuple[str, str, Path]:
    ext = mimetypes.guess_extension(content_type.split(";")[0].strip()) or ".png"
    file_id = str(uuid4())
    out_dir = _user_dir(user_id)
    out_dir.mkdir(parents=True, exist_ok=True)
    dest = out_dir / f"{file_id}{ext}"
    dest.write_bytes(data)
    return file_id, dest.name, dest


async def start() -> None:
    global _client, _account_status_name
    if not configured():
        return
    if _client is not None and getattr(_client, "_running", False):
        return

    gemini_mod = try_import("gemini_webapi")
    if gemini_mod is None:
        logger.warning("gemini-webapi 未安装，Gemini 生图接口不可用")
        return

    settings = get_settings()
    Path(settings.gemini_image_dir).mkdir(parents=True, exist_ok=True)

    client_kwargs: dict[str, Any] = {
        "secure_1psid": settings.gemini_secure_1psid,
        "secure_1psidts": settings.gemini_secure_1psidts,
    }
    if settings.gemini_proxy:
        client_kwargs["proxy"] = settings.gemini_proxy
    client = gemini_mod.GeminiClient(**client_kwargs)
    client.timeout = float(settings.gemini_timeout_sec)
    client.watchdog_timeout = float(settings.gemini_watchdog_timeout_sec)
    try:
        await client.init()
        _client = client
        _account_status_name = client.account_status.name
        logger.info("Gemini 生图客户端已启动，账号状态: %s", _account_status_name)
    except Exception as exc:
        logger.warning("Gemini 生图客户端启动失败: %s", exc)
        await _safe_close(client)


async def stop() -> None:
    global _client, _account_status_name
    if _client is not None:
        await _safe_close(_client)
        _client = None
        _account_status_name = None


async def _safe_close(client: Any) -> None:
    if hasattr(client, "close"):
        try:
            await client.close()
        except Exception:
            pass


async def _ensure_client() -> Any:
    global _client, _account_status_name
    if _client is not None and getattr(_client, "_running", False):
        return _client

    async with _init_lock:
        if _client is not None and getattr(_client, "_running", False):
            return _client
        if not configured():
            raise RuntimeError(
                "Gemini 生图未配置，请在 .env 中设置 GEMINI_SECURE_1PSID / GEMINI_SECURE_1PSIDTS"
            )
        await start()
        if _client is None:
            raise RuntimeError("Gemini 生图客户端初始化失败，请检查 Cookie、代理或 gemini-webapi 安装")
        return _client


def _build_prompt(prompt: str, force_generate: bool) -> str:
    if not force_generate:
        return prompt.strip()
    keywords = ("生成", "画一张", "画个", "绘制", "generate", "draw", "create an image", "create a")
    lowered = prompt.lower()
    if any(k in prompt or k in lowered for k in keywords):
        return f"请用 AI 生成图片，不要搜索网页图片。{prompt.strip()}"
    return f"请用 AI 生成图片，不要搜索网页图片：{prompt.strip()}"


async def _download_image_bytes(img: Any, *, full_size: bool) -> tuple[bytes, str]:
    from gemini_webapi import GeneratedImage
    from gemini_webapi.constants import Headers

    client = await _ensure_client()
    session = client.client
    if session is None:
        raise RuntimeError("Gemini HTTP 会话未建立")

    url = img.url
    if isinstance(img, GeneratedImage) and full_size:
        if all([img.client_ref, img.cid, img.rid, img.rcid, img.image_id]):
            try:
                original_url = await img.client_ref._get_full_size_image(
                    cid=img.cid,
                    rid=img.rid,
                    rcid=img.rcid,
                    image_id=img.image_id,
                )
                if original_url:
                    req_url = f"{original_url}=d-I?alr=yes"
                    r1 = await session.get(req_url, headers=Headers.REFERER.value)
                    r1.raise_for_status()
                    r2 = await session.get(r1.text, headers=Headers.REFERER.value)
                    r2.raise_for_status()
                    url = r2.text
            except Exception as exc:
                logger.debug("拉取高清原图失败，回退预览 URL: %s", exc)

        if "=s1024-rj" in url:
            url = url.replace("=s1024-rj", "=s2048-rj")
        elif "=s2048-rj" not in url:
            url += "=s2048-rj"

    response = await session.get(url, headers=Headers.REFERER.value)
    response.raise_for_status()
    content_type = response.headers.get("content-type", "image/png").split(";")[0].strip()
    return response.content, content_type or "image/png"


def status() -> dict[str, Any]:
    from gemini_webapi.constants import AccountStatus

    settings = get_settings()
    status_name = account_status_name()
    available = status_name == AccountStatus.AVAILABLE.name if status_name else False
    return {
        "configured": configured(),
        "ready": is_ready(),
        "account_status": status_name,
        "available": available,
        "proxy": bool(settings.gemini_proxy),
        "package_installed": try_import("gemini_webapi") is not None,
        "storage_dir": settings.gemini_image_dir,
    }


async def generate_image(
    prompt: str,
    user_id: str,
    *,
    force_generate: bool = True,
    full_size: bool = True,
    storage_mode: Literal["disk", "memory", "both"] = "disk",
    api_prefix: str = "/api/v1",
) -> dict[str, Any]:
    from gemini_webapi import GeneratedImage
    from gemini_webapi.constants import AccountStatus

    async with _lock:
        client = await _ensure_client()
        global _account_status_name
        _account_status_name = client.account_status.name

        if client.account_status == AccountStatus.UNAUTHENTICATED:
            raise RuntimeError(
                "Gemini Cookie 已过期或未登录，请更新 GEMINI_SECURE_1PSID / GEMINI_SECURE_1PSIDTS"
            )
        if client.account_status != AccountStatus.AVAILABLE:
            logger.warning("Gemini 账号状态: %s", client.account_status.name)

        final_prompt = _build_prompt(prompt, force_generate)
        response = await client.generate_content(final_prompt)

    need_bytes = storage_mode in ("disk", "both", "memory")
    images_out: list[dict[str, Any]] = []
    for img in response.images or []:
        source: Literal["generated", "web"] = (
            "generated" if isinstance(img, GeneratedImage) else "web"
        )
        item: dict[str, Any] = {
            "source": source,
            "content_type": "image/png",
            "base64": None,
            "url": img.url,
            "file_id": None,
            "filename": None,
            "download_path": None,
            "size_bytes": None,
            "title": getattr(img, "title", "") or "",
            "alt": getattr(img, "alt", "") or "",
        }

        if need_bytes:
            data, content_type = await _download_image_bytes(img, full_size=full_size)
            item["content_type"] = content_type
            item["size_bytes"] = len(data)

            if storage_mode in ("disk", "both"):
                file_id, filename, _ = _save_image_bytes(user_id, data, content_type)
                item["file_id"] = file_id
                item["filename"] = filename
                item["download_path"] = f"{api_prefix}/gemini-image/files/{file_id}"

            if storage_mode in ("memory", "both"):
                item["base64"] = base64.b64encode(data).decode("ascii")

        images_out.append(item)

    return {
        "text": response.text or None,
        "images": images_out,
        "image_count": len(images_out),
        "storage_mode": storage_mode,
    }
