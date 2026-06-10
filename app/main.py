import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.api.router import api_router
from app.config import get_settings
from app.core.openapi import setup_openapi, swagger_ui_parameters
from app.services import gemini_image_service, playwright_service

logger = logging.getLogger(__name__)

SWAGGER_JS_URL = "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"
SWAGGER_CSS_URL = "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css"


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    if settings.playwright_enabled:
        try:
            await playwright_service.start()
            logger.info("Playwright 后台沙箱已启动（headless Chromium）")
        except Exception as exc:
            logger.warning("Playwright 启动失败，相关接口不可用: %s", exc)
    else:
        logger.info("Playwright 未启用（PLAYWRIGHT_ENABLED=false），/playwright 接口将返回 503")
    try:
        await gemini_image_service.start()
    except Exception as exc:
        logger.warning("Gemini 生图客户端启动失败: %s", exc)
    yield
    try:
        await gemini_image_service.stop()
    except Exception:
        pass
    if settings.playwright_enabled:
        try:
            await playwright_service.stop()
        except Exception:
            pass


def create_app() -> FastAPI:
    settings = get_settings()
    docs_kwargs: dict = {}
    if settings.docs_enabled:
        docs_kwargs = {
            "docs_url": settings.docs_url,
            "redoc_url": settings.redoc_url,
            "openapi_url": settings.openapi_url,
            "swagger_ui_parameters": swagger_ui_parameters(),
            "swagger_js_url": SWAGGER_JS_URL,
            "swagger_css_url": SWAGGER_CSS_URL,
        }
    else:
        docs_kwargs = {"docs_url": None, "redoc_url": None, "openapi_url": None}

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
        **docs_kwargs,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    setup_openapi(app)
    app.include_router(api_router, prefix=settings.api_prefix)

    @app.get("/health", tags=["system"])
    async def health():
        return {"status": "ok", "service": settings.app_name, "docs": settings.docs_url}

    @app.get("/", include_in_schema=False)
    async def root():
        if settings.docs_enabled:
            return RedirectResponse(url=settings.docs_url)
        return {"service": settings.app_name, "health": "/health"}

    return app


app = create_app()
