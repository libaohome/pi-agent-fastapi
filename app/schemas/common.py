from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


class MarkItDownUrlRequest(BaseModel):
    url: HttpUrl


class MarkItDownResponse(BaseModel):
    markdown: str = Field(description="提取的正文内容（Markdown 或纯文本，见 format 字段）")
    source: str
    format: Literal["markdown", "text"] = Field(
        description="内容格式：markdown 含标题/列表等结构；text 为纯文本抽取",
    )
    method: str | None = Field(
        default=None,
        description="实际使用的提取策略：markitdown / trafilatura / playwright_markdownify 等",
    )


class WhisperResponse(BaseModel):
    language: str | None = None
    duration: float | None = None
    text: str
    segments: list[dict] = Field(default_factory=list)


class TripleRequest(BaseModel):
    subject: str
    predicate: str
    obj: str = Field(alias="object")
    graph_id: str | None = None

    model_config = {"populate_by_name": True}


class GraphQueryRequest(BaseModel):
    entity: str
    depth: int = Field(default=1, ge=1, le=5)
    graph_id: str | None = None


class FeishuMessageRequest(BaseModel):
    receive_id: str
    text: str
    receive_id_type: str = "open_id"


class WeComMessageRequest(BaseModel):
    user_id: str
    content: str


class CozeChatRequest(BaseModel):
    bot_id: str
    query: str
    stream: bool = False


class CozeWorkflowRequest(BaseModel):
    workflow_id: str
    parameters: dict = Field(default_factory=dict)


class N8nWebhookRequest(BaseModel):
    workflow_path: str
    payload: dict = Field(default_factory=dict)


class ImageGenerationRequest(BaseModel):
    prompt: str
    model: str | None = None
    size: str = "1024x1024"
    n: int = Field(default=1, ge=1, le=4)


class VideoGenerationRequest(BaseModel):
    prompt: str
    model: str | None = None
    duration: int = Field(default=5, ge=1, le=60)


class EdgeTtsVoice(BaseModel):
    name: str
    short_name: str
    gender: str
    locale: str
    friendly_name: str


class EdgeTtsVoicesResponse(BaseModel):
    voices: list[EdgeTtsVoice]


class EdgeTtsSynthesizeRequest(BaseModel):
    text: str = Field(min_length=1, max_length=5000)
    voice: str | None = Field(default=None, description="语音名称，如 zh-CN-XiaoxiaoNeural")
    rate: str = Field(default="+0%", description="语速，如 +10% / -20%")
    volume: str = Field(default="+0%", description="音量，如 +10% / -10%")
    pitch: str = Field(default="+0Hz", description="音调，如 +5Hz / -5Hz")
    stream: bool = Field(default=False, description="是否以流式返回音频（二进制模式）")
    return_base64: bool = Field(
        default=False,
        description="为 true 时返回 JSON（含 base64 音频），便于 Swagger 调试；默认返回 MP3 二进制",
    )


class EdgeTtsSynthesizeResponse(BaseModel):
    audio_base64: str = Field(description="MP3 音频的 Base64 编码")
    content_type: str = Field(default="audio/mpeg")
    size_bytes: int = Field(description="解码后音频字节数")
    voice: str = Field(description="实际使用的发音人")


class LangExtractItem(BaseModel):
    extraction_class: str
    extraction_text: str
    attributes: dict[str, str | list[str]] = Field(default_factory=dict)


class LangExtractExample(BaseModel):
    text: str
    extractions: list[LangExtractItem]


class LangExtractRequest(BaseModel):
    text: str | None = Field(default=None, description="待抽取文本")
    url: str | None = Field(default=None, description="远程文本 URL（与 text 二选一）")
    prompt_description: str = Field(min_length=1)
    examples: list[LangExtractExample] = Field(min_length=1)
    provider: str | None = Field(
        default=None,
        description="模型提供商：openai / gemini / ollama，默认读配置",
    )
    model_id: str | None = Field(default=None, description="模型 ID")
    model_url: str | None = Field(default=None, description="Ollama 服务地址")
    extraction_passes: int = Field(default=1, ge=1, le=5)
    max_workers: int = Field(default=10, ge=1, le=50)
    max_char_buffer: int = Field(default=1000, ge=200, le=10000)
    language_model_params: dict | None = Field(
        default=None,
        description="透传 LangExtract language_model_params（如 batch、vertexai）",
    )


class LangExtractResponse(BaseModel):
    text: str | None = None
    extractions: list[dict] = Field(default_factory=list)
    grounded_count: int = 0
    total_count: int = 0


class LangExtractVisualizeResponse(LangExtractResponse):
    html: str


class PlaywrightPageRequest(BaseModel):
    url: str
    wait_until: str = Field(
        default="networkidle",
        description="load | domcontentloaded | networkidle | commit",
    )
    timeout_ms: int | None = Field(default=None, ge=1000, le=120000)
    extract: str = Field(default="text", description="text | html | links | all")
    selector: str | None = Field(default=None, description="仅抽取指定选择器文本")


class PlaywrightPageResponse(BaseModel):
    url: str
    title: str
    text: str | None = None
    html: str | None = None
    links: list[dict[str, str]] = Field(default_factory=list)


class PlaywrightScreenshotRequest(BaseModel):
    url: str
    full_page: bool = False
    wait_until: str = "networkidle"
    timeout_ms: int | None = Field(default=None, ge=1000, le=120000)
    return_base64: bool = False


class PlaywrightPdfRequest(BaseModel):
    url: str
    wait_until: str = "networkidle"
    timeout_ms: int | None = Field(default=None, ge=1000, le=120000)
    return_base64: bool = False


class PlaywrightAction(BaseModel):
    type: str = Field(description="click | fill | wait | wait_for_selector | evaluate")
    selector: str | None = None
    value: str | None = None
    script: str | None = None
    timeout_ms: int | None = Field(default=None, ge=100, le=120000)


class PlaywrightRunRequest(BaseModel):
    url: str
    wait_until: str = "networkidle"
    timeout_ms: int | None = Field(default=None, ge=1000, le=120000)
    actions: list[PlaywrightAction] = Field(default_factory=list)
    extract_text: bool = True
    extract_html: bool = False
    extract_selector: str | None = None


class PlaywrightTaskSubmitRequest(BaseModel):
    type: str = Field(description="page | screenshot | pdf | run")
    payload: dict = Field(default_factory=dict)


class PlaywrightTaskResponse(BaseModel):
    task_id: str
    status: str = "pending"
    result: dict | None = None
    error: str | None = None
    created_at: str | None = None
    completed_at: str | None = None


class YtdlpInfoRequest(BaseModel):
    url: str


class YtdlpDownloadRequest(BaseModel):
    url: str
    format: str | None = Field(
        default=None,
        description="yt-dlp format 表达式，如 best / bestaudio / 137+140",
    )
    audio_only: bool = False
    audio_format: str = "mp3"
    audio_quality: str = "192"
    subtitles: bool = False
    subtitle_langs: list[str] = Field(default_factory=lambda: ["zh", "en"])
    max_filesize_mb: int | None = Field(default=None, ge=1, le=2048)
    keep_files: bool = True


class YtdlpTaskSubmitRequest(BaseModel):
    payload: dict = Field(default_factory=dict)


class YtdlpTaskResponse(BaseModel):
    task_id: str
    status: str = "pending"
    result: dict | None = None
    error: str | None = None
    created_at: str | None = None
    completed_at: str | None = None


class FfmpegTranscodeRequest(BaseModel):
    output_format: str = "mp4"
    video_codec: str = "libx264"
    audio_codec: str = "aac"
    crf: int = Field(default=23, ge=0, le=51)


class FfmpegExtractAudioRequest(BaseModel):
    audio_format: str = "mp3"
    audio_bitrate: str = "192k"


class OcrLine(BaseModel):
    text: str
    confidence: float
    box: list[list[float]]


class OcrResponse(BaseModel):
    text: str
    lines: list[OcrLine] = Field(default_factory=list)
    line_count: int = 0


class NlpSegmentRequest(BaseModel):
    text: str = Field(min_length=1, max_length=50000)
    engine: str = Field(default="jieba", description="jieba | pkuseg")
    cut_all: bool = False
    use_hmm: bool = True
    extract_keywords: bool = False
    top_k: int = Field(default=10, ge=1, le=100)
    model_name: str = "default"
    postag: bool = False


class NlpSegmentResponse(BaseModel):
    engine: str
    words: list[str] | None = None
    tokens: list[dict] | None = None
    word_count: int = 0
    keywords: list[dict] | None = None


class ExtractWebUrlRequest(BaseModel):
    url: str
    favor_precision: bool = True


class ExtractWebHtmlRequest(BaseModel):
    html: str = Field(min_length=1)
    url: str | None = None
    favor_precision: bool = True


class ExtractWebResponse(BaseModel):
    text: str
    title: str | None = None
    author: str | None = None
    url: str | None = None
    date: str | None = None
    description: str | None = None
    sitename: str | None = None
    language: str | None = None


class EmbeddingEncodeRequest(BaseModel):
    texts: list[str] = Field(min_length=1, max_length=256)
    normalize: bool = True


class EmbeddingEncodeResponse(BaseModel):
    model: str
    count: int
    dimension: int
    embeddings: list[list[float]]


class EmbeddingSimilarityRequest(BaseModel):
    text_a: str = Field(min_length=1)
    text_b: str = Field(min_length=1)


class EmbeddingSimilarityResponse(BaseModel):
    model: str
    similarity: float


class WhisperxResponse(BaseModel):
    language: str | None = None
    text: str
    segments: list[dict] = Field(default_factory=list)
    speakers: list[dict] = Field(default_factory=list)
    segment_count: int = 0


class PresidioAnalyzeRequest(BaseModel):
    text: str = Field(min_length=1, max_length=100000)
    language: str | None = None


class PresidioAnonymizeRequest(BaseModel):
    text: str = Field(min_length=1, max_length=100000)
    language: str | None = None


class PresidioEntity(BaseModel):
    type: str
    start: int
    end: int
    score: float
    text: str


class PresidioAnalyzeResponse(BaseModel):
    language: str
    entity_count: int
    entities: list[PresidioEntity]
