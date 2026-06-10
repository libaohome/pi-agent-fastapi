from typing import Any

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from typing import Any

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

# 按 Swagger UI 分组顺序定义；x-tagGroups 见 build_openapi_schema
OPENAPI_TAG_GROUPS: list[dict[str, Any]] = [
    {
        "name": "文档处理",
        "tags": ["markitdown", "pdf", "ocr", "document", "extract-web"],
    },
    {
        "name": "图片",
        "tags": ["image"],
    },
    {
        "name": "语音",
        "tags": ["whisper", "whisperx", "edge-tts", "audio-tools"],
    },
    {
        "name": "向量化",
        "tags": ["embeddings"],
    },
    {
        "name": "合规",
        "tags": ["presidio"],
    },
    {
        "name": "视频",
        "tags": ["ytdlp", "ffmpeg", "video-tools"],
    },
    {
        "name": "AI 抽取",
        "tags": ["langextract", "nlp", "knowledge-graph"],
    },
    {
        "name": "AI 生成",
        "tags": ["media", "gemini-image"],
    },
    {
        "name": "自动化",
        "tags": [
            "playwright",
            "integrations-feishu",
            "integrations-wecom",
            "integrations-coze",
            "integrations-n8n",
        ],
    },
    {
        "name": "系统",
        "tags": ["system"],
    },
]

OPENAPI_TAGS: list[dict[str, str]] = [
    # 文档处理
    {"name": "markitdown", "description": "文档/网页转 Markdown（MarkItDown）"},
    {"name": "pdf", "description": "PDF 文本/图片/表格提取（PyMuPDF、pdfplumber、camelot）"},
    {"name": "ocr", "description": "图片 OCR（PaddleOCR）"},
    {"name": "document", "description": "统一文档解析（unstructured：PDF/Word/PPT/邮件等）"},
    {"name": "extract-web", "description": "网页正文抽取（trafilatura，可配合 Playwright）"},
    # 图片
    {"name": "image", "description": "图片处理（rembg 抠图去背景）"},
    # 语音
    {"name": "whisper", "description": "语音转文字（Faster Whisper）"},
    {"name": "whisperx", "description": "高精度转写 + 时间戳 + 说话人分离（whisperx）"},
    {"name": "edge-tts", "description": "文字转语音（Edge TTS）"},
    {"name": "audio-tools", "description": "音频分析、切片、音轨分离（librosa、pydub、demucs）"},
    # 向量化
    {"name": "embeddings", "description": "本地文本向量化与相似度（sentence-transformers）"},
    # 合规
    {"name": "presidio", "description": "PII 检测与脱敏（Microsoft Presidio）"},
    # 视频
    {"name": "ytdlp", "description": "视频/音频下载（yt-dlp）"},
    {"name": "ffmpeg", "description": "媒体探测、转码、提取音频（ffmpeg）"},
    {"name": "video-tools", "description": "视频分镜、裁剪、缩略图（moviepy、scenedetect）"},
    # AI 抽取
    {"name": "langextract", "description": "LLM 结构化信息抽取（LangExtract）"},
    {"name": "nlp", "description": "中文分词与关键词（jieba、pkuseg）"},
    {"name": "knowledge-graph", "description": "知识图谱三元组存储与邻域查询"},
    # AI 生成
    {"name": "media", "description": "图片/视频生成（OpenAI 兼容网关）"},
    {"name": "gemini-image", "description": "Gemini 网页端 AI 生图（gemini-webapi + Cookie）"},
    # 自动化
    {"name": "playwright", "description": "后台无头沙箱浏览器自动化（Chromium）"},
    {"name": "integrations-feishu", "description": "飞书集成（消息推送等）"},
    {"name": "integrations-wecom", "description": "企业微信集成"},
    {"name": "integrations-coze", "description": "Coze Studio 集成"},
    {"name": "integrations-n8n", "description": "n8n Webhook 集成"},
    # 系统
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
- **图片**：image
- **语音**：whisper、whisperx、edge-tts、audio-tools
- **向量化**：embeddings
- **合规**：presidio
- **视频**：ytdlp、ffmpeg、video-tools
- **AI 抽取**：langextract、nlp、knowledge-graph
- **AI 生成**：media、gemini-image
- **自动化**：playwright、integrations（飞书 / 企微 / Coze / n8n）
- **系统**：health
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
    schema["x-tagGroups"] = OPENAPI_TAG_GROUPS
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
