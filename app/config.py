from functools import lru_cache

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Pi Agent FastAPI"
    app_version: str = "0.1.0"
    debug: bool = False
    api_prefix: str = "/api/v1"
    cors_origins: str = "http://localhost:3000"

    # Swagger UI / OpenAPI 文档
    docs_enabled: bool = True
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"
    openapi_url: str = "/openapi.json"

    # Supabase — 与 pi-agent 共用同一项目（兼容 pi-agent 环境变量名）
    supabase_url: str = Field(
        validation_alias=AliasChoices("SUPABASE_URL", "NEXT_PUBLIC_SUPABASE_URL"),
    )
    supabase_anon_key: str = Field(
        validation_alias=AliasChoices(
            "SUPABASE_ANON_KEY",
            "NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY",
        ),
    )
    supabase_service_role_key: str

    # Whisper
    whisper_model_size: str = "base"
    whisper_device: str = "cpu"
    whisper_compute_type: str = "int8"

    # Edge TTS
    edge_tts_default_voice: str = "zh-CN-XiaoxiaoNeural"

    # 知识图谱本地存储目录
    knowledge_graph_dir: str = ".data/knowledge-graphs"

    # 飞书
    feishu_app_id: str | None = None
    feishu_app_secret: str | None = None

    # 企业微信
    wecom_corp_id: str | None = None
    wecom_agent_id: str | None = None
    wecom_secret: str | None = None

    # Coze Studio
    coze_api_base: str = "https://api.coze.cn"
    coze_api_token: str | None = None

    # n8n
    n8n_webhook_base: str | None = None
    n8n_api_key: str | None = None

    # 图片/视频生成（OpenAI 兼容网关，可与 pi-agent 共用）
    media_openai_base_url: str | None = None
    media_openai_api_key: str | None = None
    default_image_model: str = "dall-e-3"
    default_video_model: str = "kling-v1"

    # LangExtract（结构化信息抽取）
    langextract_default_provider: str = "openai"
    langextract_default_model: str = Field(
        default="Qwen/Qwen3-235B-A22B",
        validation_alias=AliasChoices(
            "LANGEXTRACT_DEFAULT_MODEL",
            "DEFAULT_MODEL_NAME",
        ),
    )
    langextract_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("LANGEXTRACT_API_KEY", "GEMINI_API_KEY"),
    )
    langextract_openai_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("LANGEXTRACT_OPENAI_API_KEY", "OPENAI_API_KEY"),
    )
    langextract_openai_base_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("LANGEXTRACT_OPENAI_BASE_URL", "OPENAI_BASE_URL"),
    )
    langextract_ollama_url: str = "http://localhost:11434"

    # Playwright 后台沙箱
    playwright_headless: bool = True
    playwright_chromium_sandbox: bool = True
    playwright_max_concurrent: int = Field(default=3, ge=1, le=20)
    playwright_timeout_ms: int = Field(default=30000, ge=1000, le=120000)
    playwright_navigation_timeout_ms: int = Field(default=45000, ge=1000, le=180000)
    playwright_viewport_width: int = 1280
    playwright_viewport_height: int = 720
    playwright_locale: str = "zh-CN"
    playwright_user_agent: str | None = None
    playwright_sandbox_dir: str = ".data/playwright-sandbox"
    playwright_cleanup_sandbox: bool = True
    playwright_accept_downloads: bool = False
    playwright_record_har: bool = False
    playwright_block_private_network: bool = True
    playwright_allowed_hosts: str | None = Field(
        default=None,
        description="逗号分隔域名白名单，留空则仅拦截内网",
    )

    # yt-dlp / ffmpeg
    ytdlp_download_dir: str = ".data/ytdlp-downloads"
    ytdlp_allow_playlist: bool = False
    ytdlp_socket_timeout: int = Field(default=30, ge=5, le=300)
    ytdlp_retries: int = Field(default=3, ge=0, le=10)
    ytdlp_proxy: str | None = None
    ytdlp_cookies_file: str | None = None
    ytdlp_cleanup_after_days: int = Field(default=7, ge=0, le=365)
    ffmpeg_path: str | None = None
    ffprobe_path: str | None = None
    ffmpeg_timeout_sec: int = Field(default=600, ge=10, le=3600)

    # PaddleOCR
    paddleocr_lang: str = "ch"
    paddleocr_use_angle_cls: bool = True

    # 视频/音频处理工作目录
    video_work_dir: str = ".data/video-work"
    audio_work_dir: str = ".data/audio-work"
    demucs_timeout_sec: int = Field(default=1800, ge=60, le=7200)

    # sentence-transformers
    embedding_model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"

    # whisperx
    whisperx_model: str = "base"
    whisperx_device: str = "cpu"
    whisperx_compute_type: str = "int8"
    whisperx_batch_size: int = Field(default=8, ge=1, le=64)
    whisperx_align: bool = True
    whisperx_hf_token: str | None = Field(
        default=None,
        validation_alias=AliasChoices("WHISPERX_HF_TOKEN", "HF_TOKEN"),
    )

    # presidio
    presidio_language: str = "zh"

    # Gemini 网页端生图（gemini-webapi + Cookie）
    gemini_secure_1psid: str | None = None
    gemini_secure_1psidts: str | None = None
    gemini_proxy: str | None = None
    gemini_timeout_sec: int = Field(default=600, ge=60, le=1800)
    gemini_watchdog_timeout_sec: int = Field(default=180, ge=30, le=600)
    gemini_image_dir: str = ".data/gemini-images"

    @field_validator("gemini_proxy", mode="before")
    @classmethod
    def _normalize_gemini_proxy(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if isinstance(value, str) and not value.strip():
            return None
        return value.strip() if isinstance(value, str) else value

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
