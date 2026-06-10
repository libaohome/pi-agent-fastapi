import asyncio
import base64
import shutil
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from playwright.async_api import Browser, BrowserContext, Page, Playwright, async_playwright

from app.config import get_settings
from app.schemas.common import PlaywrightPageRequest, PlaywrightRunRequest
from app.services.playwright_sandbox import SandboxError, create_sandbox_dir, validate_target_url

_browser: Browser | None = None
_playwright: Playwright | None = None
_semaphore: asyncio.Semaphore | None = None
_tasks: dict[str, dict[str, Any]] = {}


@dataclass
class PlaywrightSession:
    user_id: str
    sandbox_dir: Any
    context: BrowserContext
    page: Page


@dataclass
class PlaywrightPageResult:
    url: str
    title: str
    text: str | None = None
    html: str | None = None
    links: list[dict[str, str]] = field(default_factory=list)


async def start() -> None:
    global _browser, _playwright, _semaphore
    settings = get_settings()
    if not settings.playwright_enabled:
        return
    if _browser is not None:
        return
    _semaphore = asyncio.Semaphore(settings.playwright_max_concurrent)
    _playwright = await async_playwright().start()
    _browser = await _playwright.chromium.launch(
        headless=settings.playwright_headless,
        chromium_sandbox=settings.playwright_chromium_sandbox,
        args=[
            "--disable-dev-shm-usage",
            "--no-first-run",
            "--no-default-browser-check",
        ],
    )


async def stop() -> None:
    global _browser, _playwright, _semaphore
    if _browser is not None:
        await _browser.close()
        _browser = None
    if _playwright is not None:
        await _playwright.stop()
        _playwright = None
    _semaphore = None


def is_ready() -> bool:
    return _browser is not None and _browser.is_connected()


@asynccontextmanager
async def sandbox_session(user_id: str):
    settings = get_settings()
    if _browser is None or _semaphore is None:
        raise RuntimeError("Playwright 未启动，请检查 Chromium 是否已安装")

    sandbox_dir = create_sandbox_dir(user_id)
    async with _semaphore:
        context = await _browser.new_context(
            viewport={
                "width": settings.playwright_viewport_width,
                "height": settings.playwright_viewport_height,
            },
            accept_downloads=settings.playwright_accept_downloads,
            java_script_enabled=True,
            locale=settings.playwright_locale,
            user_agent=settings.playwright_user_agent or None,
            record_har_path=str(sandbox_dir / "session.har") if settings.playwright_record_har else None,
        )
        context.set_default_timeout(settings.playwright_timeout_ms)
        context.set_default_navigation_timeout(settings.playwright_navigation_timeout_ms)
        page = await context.new_page()
        session = PlaywrightSession(
            user_id=user_id,
            sandbox_dir=sandbox_dir,
            context=context,
            page=page,
        )
        try:
            yield session
        finally:
            await context.close()
            if settings.playwright_cleanup_sandbox:
                shutil.rmtree(sandbox_dir, ignore_errors=True)


async def fetch_rendered_content(
    url: str,
    *,
    wait_until: str = "networkidle",
    timeout_ms: int | None = None,
    user_id: str = "_markitdown",
) -> tuple[str, str]:
    """无头浏览器渲染页面，返回 (html, body_text)。"""
    settings = get_settings()
    target = validate_target_url(url)
    async with sandbox_session(user_id) as session:
        await session.page.goto(
            target,
            wait_until=wait_until,
            timeout=timeout_ms or settings.playwright_navigation_timeout_ms,
        )
        html = await session.page.content()
        text = await session.page.inner_text("body")
        return html, text


async def fetch_page(user_id: str, request: PlaywrightPageRequest) -> PlaywrightPageResult:
    url = validate_target_url(request.url)
    async with sandbox_session(user_id) as session:
        response = await session.page.goto(
            url,
            wait_until=request.wait_until,
            timeout=request.timeout_ms,
        )
        if response is None:
            raise RuntimeError("页面导航失败")

        title = await session.page.title()
        result = PlaywrightPageResult(
            url=session.page.url,
            title=title,
        )
        if request.extract in {"text", "all"}:
            result.text = await session.page.inner_text("body")
        if request.extract in {"html", "all"}:
            result.html = await session.page.content()
        if request.extract in {"links", "all"}:
            links = await session.page.eval_on_selector_all(
                "a[href]",
                "els => els.map(a => ({href: a.href, text: (a.innerText || '').trim()}))",
            )
            result.links = links
        if request.selector:
            result.text = await session.page.inner_text(request.selector)
        return result


async def take_screenshot(
    user_id: str,
    url: str,
    *,
    full_page: bool = False,
    wait_until: str = "networkidle",
    timeout_ms: int | None = None,
) -> bytes:
    settings = get_settings()
    target = validate_target_url(url)
    async with sandbox_session(user_id) as session:
        await session.page.goto(
            target,
            wait_until=wait_until,
            timeout=timeout_ms or settings.playwright_navigation_timeout_ms,
        )
        return await session.page.screenshot(full_page=full_page, type="png")


async def export_pdf(
    user_id: str,
    url: str,
    *,
    wait_until: str = "networkidle",
    timeout_ms: int | None = None,
) -> bytes:
    settings = get_settings()
    target = validate_target_url(url)
    async with sandbox_session(user_id) as session:
        await session.page.goto(
            target,
            wait_until=wait_until,
            timeout=timeout_ms or settings.playwright_navigation_timeout_ms,
        )
        return await session.page.pdf(format="A4", print_background=True)


async def run_actions(user_id: str, request: PlaywrightRunRequest) -> dict[str, Any]:
    url = validate_target_url(request.url)
    logs: list[str] = []
    async with sandbox_session(user_id) as session:
        page = session.page
        await page.goto(
            url,
            wait_until=request.wait_until,
            timeout=request.timeout_ms,
        )
        for step in request.actions:
            action = step.type
            if action == "click":
                await page.click(step.selector or "", timeout=step.timeout_ms)
                logs.append(f"click: {step.selector}")
            elif action == "fill":
                await page.fill(step.selector or "", step.value or "", timeout=step.timeout_ms)
                logs.append(f"fill: {step.selector}")
            elif action == "wait_for_selector":
                await page.wait_for_selector(step.selector or "", timeout=step.timeout_ms)
                logs.append(f"wait_for_selector: {step.selector}")
            elif action == "wait":
                await page.wait_for_timeout(step.timeout_ms or 1000)
                logs.append(f"wait: {step.timeout_ms}ms")
            elif action == "evaluate":
                if not step.script:
                    raise ValueError("evaluate 需要 script")
                await page.evaluate(step.script)
                logs.append("evaluate: custom script")
            else:
                raise ValueError(f"不支持的操作: {action}")

        payload: dict[str, Any] = {
            "url": page.url,
            "title": await page.title(),
            "logs": logs,
        }
        if request.extract_text:
            payload["text"] = await page.inner_text("body")
        if request.extract_html:
            payload["html"] = await page.content()
        if request.extract_selector:
            payload["selector_text"] = await page.inner_text(request.extract_selector)
        return payload


def _create_task_record(user_id: str, task_type: str, payload: dict) -> str:
    task_id = str(uuid4())
    _tasks[task_id] = {
        "id": task_id,
        "user_id": user_id,
        "type": task_type,
        "status": "pending",
        "payload": payload,
        "result": None,
        "error": None,
        "created_at": datetime.now(UTC).isoformat(),
        "completed_at": None,
    }
    return task_id


async def _execute_background_task(task_id: str) -> None:
    task = _tasks.get(task_id)
    if not task:
        return
    task["status"] = "running"
    try:
        user_id = task["user_id"]
        task_type = task["type"]
        payload = task["payload"]
        if task_type == "page":
            result = await fetch_page(user_id, PlaywrightPageRequest(**payload))
            task["result"] = {
                "url": result.url,
                "title": result.title,
                "text": result.text,
                "html": result.html,
                "links": result.links,
            }
        elif task_type == "screenshot":
            png = await take_screenshot(user_id, **payload)
            task["result"] = {"image_base64": base64.b64encode(png).decode()}
        elif task_type == "pdf":
            pdf = await export_pdf(user_id, **payload)
            task["result"] = {"pdf_base64": base64.b64encode(pdf).decode()}
        elif task_type == "run":
            task["result"] = await run_actions(user_id, PlaywrightRunRequest(**payload))
        else:
            raise ValueError(f"未知任务类型: {task_type}")
        task["status"] = "completed"
    except (SandboxError, ValueError, RuntimeError) as exc:
        task["status"] = "failed"
        task["error"] = str(exc)
    except Exception as exc:
        task["status"] = "failed"
        task["error"] = f"执行失败: {exc}"
    finally:
        task["completed_at"] = datetime.now(UTC).isoformat()


def submit_background_task(user_id: str, task_type: str, payload: dict) -> str:
    task_id = _create_task_record(user_id, task_type, payload)
    asyncio.create_task(_execute_background_task(task_id))
    return task_id


def get_task(task_id: str, user_id: str) -> dict[str, Any] | None:
    task = _tasks.get(task_id)
    if not task or task["user_id"] != user_id:
        return None
    return task


def list_tasks(user_id: str, limit: int = 20) -> list[dict[str, Any]]:
    items = [t for t in _tasks.values() if t["user_id"] == user_id]
    items.sort(key=lambda t: t["created_at"], reverse=True)
    return items[:limit]
