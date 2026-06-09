from typing import Any

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

OPENAPI_TAGS: list[dict[str, str]] = [
    {"name": "markitdown", "description": "文档/网页转 Markdown"},
    {"name": "whisper", "description": "语音转文字（Faster Whisper）"},
    {"name": "edge-tts", "description": "文字转语音（Edge TTS）"},
    {"name": "langextract", "description": "LLM 结构化信息抽取"},
    {"name": "playwright", "description": "后台无头沙箱浏览器自动化"},
    {"name": "ytdlp", "description": "视频/音频下载（yt-dlp）"},
    {"name": "ffmpeg", "description": "媒体探测、转码、提取音频"},
    {"name": "ocr", "description": "图片 OCR（PaddleOCR）"},
    {"name": "image", "description": "图片处理（rembg 抠图）"},
    {"name": "pdf", "description": "PDF 文本/图片/表格提取（PyMuPDF、pdfplumber、camelot）"},
    {"name": "video-tools", "description": "视频分镜、裁剪、缩略图（moviepy、scenedetect）"},
    {"name": "audio-tools", "description": "音频分析、切片、音轨分离（librosa、pydub、demucs）"},
    {"name": "nlp", "description": "中文分词（jieba、pkuseg）"},
    {"name": "extract-web", "description": "网页正文抽取（trafilatura）"},
    {"name": "document", "description": "统一文档解析（unstructured）"},
    {"name": "embeddings", "description": "本地文本向量化（sentence-transformers）"},
    {"name": "whisperx", "description": "高精度转写+时间戳+说话人分离（whisperx）"},
    {"name": "presidio", "description": "PII 检测与脱敏"},
    {"name": "knowledge-graph", "description": "知识图谱三元组与查询"},
    {"name": "integrations-feishu", "description": "飞书集成"},
    {"name": "integrations-wecom", "description": "企业微信集成"},
    {"name": "integrations-coze", "description": "Coze Studio 集成"},
    {"name": "integrations-n8n", "description": "n8n Webhook 集成"},
    {"name": "media", "description": "图片/视频生成（OpenAI 兼容网关）"},
    {"name": "gemini-image", "description": "Gemini 网页端 AI 生图（gemini-webapi + Cookie）"},
    {"name": "system", "description": "系统健康检查"},
]

OPENAPI_DESCRIPTION = """
Pi Agent Python 侧服务 API，与 **pi-agent**（Next.js）共用 Supabase 鉴权。

## 鉴权方式

点击右上角 **Authorize**，填入 Bearer Token：

| 类型 | 格式 | 获取方式 |
|------|------|---------|
| Supabase JWT | `eyJhbG...` | Web 登录后 `session.access_token` |
| API Key | `pi_xxxx...` | pi-agent 控制台创建 |

## 模块分组

- **文档处理**：markitdown、pdf、ocr、document、extract-web
- **语音**：whisper、whisperx、edge-tts、audio-tools
- **向量化**：embeddings
- **合规**：presidio
- **视频**：ytdlp、ffmpeg、video-tools
- **AI 抽取**：langextract、nlp、knowledge-graph
- **自动化**：playwright、integrations
"""

SECURITY_SCHEME = {
    "BearerAuth": {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT or API Key",
        "description": (
            "Supabase `access_token`，或 pi-agent 的 `pi_` 前缀 API Key。"
            "示例：`Authorization: Bearer eyJhbG...` 或 `Bearer pi_xxx`"
        ),
    }
}

PUBLIC_PATHS = {"/health", "/docs", "/redoc", "/openapi.json"}


def swagger_ui_parameters() -> dict[str, Any]:
    return {
        "persistAuthorization": True,
        "displayRequestDuration": True,
        "filter": True,
        "tryItOutEnabled": True,
        "docExpansion": "list",
        "defaultModelsExpandDepth": 2,
        "syntaxHighlight.theme": "monokai",
        "deepLinking": True,
    }


def build_openapi_schema(app: FastAPI) -> dict[str, Any]:
    if app.openapi_schema:
        return app.openapi_schema

    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=OPENAPI_DESCRIPTION,
        routes=app.routes,
        tags=OPENAPI_TAGS,
    )
    components = schema.setdefault("components", {})
    # 统一使用 BearerAuth，替换 FastAPI 自动生成的 HTTPBearer
    schemes = components.get("securitySchemes", {})
    schemes.pop("HTTPBearer", None)
    schemes.update(SECURITY_SCHEME)
    components["securitySchemes"] = schemes

    for path, path_item in schema.get("paths", {}).items():
        if path in PUBLIC_PATHS:
            continue
        for operation in path_item.values():
            if not isinstance(operation, dict):
                continue
            operation["security"] = [{"BearerAuth": []}]

    app.openapi_schema = schema
    return schema


def setup_openapi(app: FastAPI) -> None:
    app.openapi = lambda: build_openapi_schema(app)
