# Pi Agent FastAPI

Pi Agent 的 Python 侧服务，与 `[../pi-agent](../pi-agent)`（Next.js）共用 **Supabase 项目** 与 **鉴权 Token**。

## 职责总览

| 分组 | 模块 | 路径 | 说明 |
|------|------|------|------|
| **文档处理** | MarkItDown | `/api/v1/markitdown` | 文档/网页转 Markdown |
| | PDF 工具 | `/api/v1/pdf` | PyMuPDF / pdfplumber / camelot 文本与表格提取 |
| | PaddleOCR | `/api/v1/ocr` | 图片/PDF 扫描件 OCR |
| | unstructured | `/api/v1/document` | 统一文档解析（PDF/Word/PPT/邮件等） |
| | trafilatura | `/api/v1/extract-web` | 网页正文抽取（可配合 Playwright） |
| **图片** | rembg | `/api/v1/image` | 图片抠图去背景 |
| **语音** | Faster Whisper | `/api/v1/whisper` | 语音转文字 |
| | whisperx | `/api/v1/whisperx` | 高精度转写 + 时间戳 + 说话人分离 |
| | Edge TTS | `/api/v1/edge-tts` | 文字转语音（微软在线，无需 Key） |
| | 音频工具 | `/api/v1/audio-tools` | librosa / pydub / demucs 分析、切片、分离 |
| **向量化** | sentence-transformers | `/api/v1/embeddings` | 本地文本向量化与相似度 |
| **合规** | presidio | `/api/v1/presidio` | PII 检测与脱敏 |
| **视频** | yt-dlp | `/api/v1/ytdlp` | 视频/音频下载 |
| | ffmpeg | `/api/v1/ffmpeg` | 媒体探测、转码、提取音频 |
| | 视频工具 | `/api/v1/video-tools` | moviepy / scenedetect 裁剪、分镜、缩略图 |
| **AI 抽取** | LangExtract | `/api/v1/langextract` | LLM 结构化信息抽取 |
| | jieba | `/api/v1/nlp` | 中文分词与关键词（pkuseg 不支持 Py3.12+） |
| | 知识图谱 | `/api/v1/knowledge-graph` | 三元组存储与邻域查询 |
| **AI 生成** | 媒体生成 | `/api/v1/media` | 图片/视频（OpenAI 兼容网关） |
| | Gemini 生图 | `/api/v1/gemini-image` | Gemini 网页端 AI 生图（Cookie 鉴权） |
| **自动化** | Playwright | `/api/v1/playwright` | 后台无头沙箱浏览器（需 `PLAYWRIGHT_ENABLED=true`） |
| | 飞书 / 企微 / Coze / n8n | `/api/v1/integrations/*` | 第三方集成 |
| **系统** | 健康检查 | `/health` | 服务存活探测 |

> OCR、PDF、音视频、NLP、Top5 等扩展能力需安装：`pip install -e ".[dev,ml,top5]"`  
> 各模块 `GET /status`（如有）会返回对应库是否可用。
## 鉴权（与 pi-agent 一致）

所有 `/api/v1/`* 接口需要 `Authorization: Bearer <token>`：

1. **Supabase JWT**：Web 登录后的 `access_token`
2. **API Key**：`pi_` 前缀，与 pi-agent `api_keys` 表共用

```bash
export TOKEN="your_supabase_access_token"
# 或
export TOKEN="pi_xxxxxxxx"
```

## 快速开始

### 1. 配置与环境

```bash
cd pi-agent-fastapi
cp .env.example .env
# 填入与 pi-agent 相同的 Supabase 配置
```

### 2. 系统依赖（按需）

**ffmpeg**（yt-dlp / ffmpeg / 音视频模块需要）：

```bash
# macOS
brew install ffmpeg

# Ubuntu / Debian
sudo apt update && sudo apt install -y ffmpeg

# RHEL / CentOS（需 EPEL 或 RPM Fusion）
sudo dnf install -y ffmpeg   # 或 yum，视发行版而定

ffmpeg -version   # 确认安装
```

**ghostscript**（camelot PDF 表格提取需要）：`brew install ghostscript` / `apt install ghostscript`

**Playwright**（仅在使用 `/playwright` 时需要，且 `.env` 中 `PLAYWRIGHT_ENABLED=true`）：

```bash
playwright install chromium
playwright install-deps chromium   # Linux 系统库
```

### 3. Python 依赖

```bash
# 推荐 Python 3.11 / 3.12（3.13 下部分 ML 库可能不兼容）
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,ml,top5]"   # 含 OCR/PDF/音视频/NLP/Top5 等扩展库

# 或使用脚本：bash scripts/install-ml.sh

python -m spacy download zh_core_web_sm   # presidio 中文支持（可选）
```

### 4. 启动服务

**开发模式：**

```bash
uvicorn app.main:app --reload --port 8000
# 或
bash run.sh --dev
```

**Linux 生产部署（`run.sh`）：**

```bash
# 前台
bash run.sh

# 指定端口 /  worker 数（低内存 VPS 建议 WORKERS=1）
HOST=0.0.0.0 PORT=8000 WORKERS=1 bash run.sh

# 后台运行
nohup bash run.sh > app.log 2>&1 &
```

| 环境变量 | 默认值 | 说明 |
|---------|--------|------|
| `HOST` | `0.0.0.0` | 监听地址 |
| `PORT` | `8000` | 端口 |
| `WORKERS` | `1` | uvicorn worker 数（每 worker 独立占内存） |
| `PYTHON` | 自动检测 | 指定 Python 解释器，如 `python3.12` |

- 健康检查：`GET http://localhost:8000/health`
- 根路径 `http://localhost:8000/` 自动跳转到 Swagger UI

## API 文档（Swagger UI）


| 地址                                                    | 说明                                     |
| ----------------------------------------------------- | -------------------------------------- |
| `[/docs](http://localhost:8000/docs)`                 | **Swagger UI** — 在线调试、分组浏览、鉴权测试        |
| `[/redoc](http://localhost:8000/redoc)`               | ReDoc — 只读文档                           |
| `[/openapi.json](http://localhost:8000/openapi.json)` | OpenAPI 3.0 Schema（可导入 Postman/Apifox） |


### 在 Swagger UI 中测试接口

1. 打开 `http://localhost:8000/docs`
2. 点击右上角 **Authorize**
3. 填入 Bearer Token（Supabase `access_token` 或 `pi_` API Key）
4. 展开任意接口 → **Try it out** → 执行

文档特性：

- 按 **10 个模块分组** 折叠浏览（文档处理、图片、语音、向量化、合规、视频、AI 抽取、AI 生成、自动化、系统）
- **持久化鉴权**（刷新页面 Token 仍保留）
- 接口 **耗时显示**、关键字 **过滤搜索**
- 生产环境可通过 `DOCS_ENABLED=false` 关闭

### 低内存服务器建议

| 配置 | 建议值 | 原因 |
|------|--------|------|
| `PLAYWRIGHT_ENABLED` | `false` | Chromium 启动占用数百 MB～1GB+ |
| `WORKERS` | `1` | 每个 worker 是独立进程，内存翻倍 |
| Python 版本 | 3.11 / 3.12 | 3.13 下部分 ML 库兼容性较差 |
| 可选依赖 | 按需安装 `[dev]` 即可 | 不装 `[ml,top5]` 可减小镜像体积 |

ML 模型（whisper、OCR、rembg 等）均为 **首次调用时加载**，不会在启动时占内存；但调用后仍会临时占用大量 RAM。

### 依赖分组说明


| 安装命令                              | 包含能力                                                       |
| --------------------------------- | ---------------------------------------------------------- |
| `pip install -e ".[dev]"`         | 基础服务（markitdown、whisper、playwright 等）                      |
| `pip install -e ".[dev,ml]"`      | OCR、PDF、rembg、音视频处理、NLP                                    |
| `pip install -e ".[dev,ml,top5]"` | 额外启用 trafilatura、unstructured、embeddings、whisperx、presidio |


各模块 `GET /status` 会返回对应库是否可用。

---

## 使用手册

### 0. MarkItDown — `/api/v1/markitdown`

文档/网页转 Markdown，支持上传文件或 URL。

```bash
# 上传文件转换
curl -X POST http://localhost:8000/api/v1/markitdown/convert/file \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@report.docx"

# URL 转换
curl -X POST http://localhost:8000/api/v1/markitdown/convert/url \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com/page"}'
```

---

### 1. PaddleOCR — `/api/v1/ocr`

图片文字识别，中文效果优秀，适合扫描件、截图、拍照文档。

```bash
# 检查状态
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/ocr/status

# 识别图片
curl -X POST http://localhost:8000/api/v1/ocr/recognize \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@scan.png"
```

**响应示例：**

```json
{
  "text": "全文合并文本",
  "lines": [
    {"text": "第一行", "confidence": 0.98, "box": [[10,20],[100,20],[100,40],[10,40]]}
  ],
  "line_count": 1
}
```

**配置（`.env`）：**

```
PADDLEOCR_LANG=ch
PADDLEOCR_USE_ANGLE_CLS=true
```

---

### 2. rembg — `/api/v1/image`

去除图片背景，返回 PNG 透明底图。

```bash
curl -X POST http://localhost:8000/api/v1/image/remove-background \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@photo.jpg" \
  -o output.png
```

---

### 3. PDF 处理 — `/api/v1/pdf`

#### 3.1 PyMuPDF — 文本与图片提取

```bash
# 提取文本（可指定页码范围）
curl -X POST http://localhost:8000/api/v1/pdf/pymupdf/text \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@doc.pdf" \
  -F "page_start=1" \
  -F "page_end=5"

# 提取指定页内嵌图片（base64）
curl -X POST http://localhost:8000/api/v1/pdf/pymupdf/images \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@doc.pdf" \
  -F "page=1"
```

#### 3.2 pdfplumber — 表格提取

适合电子版 PDF、可复制文本的表格。

```bash
curl -X POST http://localhost:8000/api/v1/pdf/pdfplumber/tables \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@report.pdf" \
  -F "pages=all"
```

#### 3.3 camelot — 表格提取

适合扫描版/线条明显的表格，需系统安装 **ghostscript**。

```bash
# flavor: lattice（有框线）或 stream（无框线）
curl -X POST http://localhost:8000/api/v1/pdf/camelot/tables \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@report.pdf" \
  -F "pages=1-3" \
  -F "flavor=lattice"
```

---

### 4. 视频处理 — `/api/v1/video-tools`

基于 **moviepy** + **scenedetect**，配合 yt-dlp/ffmpeg 形成完整视频流水线。

```bash
# 分镜检测
curl -X POST http://localhost:8000/api/v1/video-tools/scenes \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@video.mp4" \
  -F "threshold=27.0"

# 裁剪片段（返回 mp4 文件）
curl -X POST http://localhost:8000/api/v1/video-tools/clip \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@video.mp4" \
  -F "start_sec=10" \
  -F "end_sec=30" \
  -o clip.mp4

# 生成缩略图
curl -X POST http://localhost:8000/api/v1/video-tools/thumbnail \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@video.mp4" \
  -F "at_sec=5" \
  -o thumb.png
```

---

### 5. 音频处理 — `/api/v1/audio-tools`

#### 5.1 librosa — 音频分析

```bash
curl -X POST http://localhost:8000/api/v1/audio-tools/librosa/analyze \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@music.mp3"
```

返回采样率、时长、节奏 BPM、RMS 等。

#### 5.2 pydub — 切片与格式转换

```bash
# 按毫秒切片
curl -X POST http://localhost:8000/api/v1/audio-tools/pydub/slice \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@podcast.mp3" \
  -F "start_ms=0" \
  -F "end_ms=60000" \
  -o clip.mp3

# 格式转换
curl -X POST http://localhost:8000/api/v1/audio-tools/pydub/convert \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@input.ogg" \
  -F "fmt=wav" \
  -o output.wav
```

#### 5.3 demucs — 人声/伴奏分离

计算密集，首次运行会下载模型。

```bash
curl -X POST http://localhost:8000/api/v1/audio-tools/demucs/separate \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@song.mp3" \
  -F "stems=vocals"
```

返回分离后文件路径列表（保存在 `.data/audio-work/{user_id}/`）。

---

### 6. 中文 NLP — `/api/v1/nlp`

#### 6.1 jieba 分词

```bash
curl -X POST http://localhost:8000/api/v1/nlp/segment \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Pi Agent 是一个智能体平台",
    "engine": "jieba",
    "extract_keywords": true,
    "top_k": 5
  }'
```

#### 6.2 pkuseg 说明

> **注意**：pkuseg 不支持 Python 3.12+（C 扩展编译失败），本项目要求 Python ≥3.11。
> 请使用 `engine: "jieba"`；如需词性标注可考虑后续接入 spaCy / HanLP。

```bash
# pkuseg 仅在 Python 3.10/3.11 环境可用（本仓库默认 3.12 请勿安装）
curl -X POST http://localhost:8000/api/v1/nlp/segment \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text":"北京大学位于北京市海淀区","engine":"jieba","extract_keywords":true}'
```

---

### 7. Playwright 后台沙箱 — `/api/v1/playwright`

无头 Chromium，独立 BrowserContext，默认拦截内网地址。

> **默认不在启动时加载**。需在 `.env` 设置 `PLAYWRIGHT_ENABLED=true` 并安装 Chromium 后重启服务；未启用时接口返回 503。

```bash
# 检查状态
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/playwright/status

curl -X POST http://localhost:8000/api/v1/playwright/page \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com","extract":"all"}'
```

后台任务：`POST /tasks` → 轮询 `GET /tasks/{id}`

---

### 8. yt-dlp / ffmpeg

```bash
# 视频信息
curl -X POST http://localhost:8000/api/v1/ytdlp/info \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://www.youtube.com/watch?v=xxxx"}'

# 后台下载音频
curl -X POST http://localhost:8000/api/v1/ytdlp/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"payload":{"url":"https://...","audio_only":true}}'

# ffmpeg 转码
curl -X POST http://localhost:8000/api/v1/ffmpeg/transcode \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@input.mkv" -F "output_format=mp4"
```

---

### 9. trafilatura 网页正文 — `/api/v1/extract-web`

配合 Playwright 使用：Playwright 抓 HTML → trafilatura 抽正文。

```bash
# 从 URL 直接抽取
curl -X POST http://localhost:8000/api/v1/extract-web/url \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com/article"}'

# 从 HTML 片段抽取（Playwright 抓取后传入）
curl -X POST http://localhost:8000/api/v1/extract-web/html \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"html":"<html>...</html>","url":"https://example.com"}'
```

---

### 10. unstructured 文档解析 — `/api/v1/document`

统一解析 PDF、Word、PPT、Excel、HTML、邮件等。

```bash
curl -X POST http://localhost:8000/api/v1/document/parse \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@report.pdf" \
  -F "strategy=auto"
```

返回结构化 `elements` 列表和合并后的 `text`，可直接送入知识库。

---

### 11. sentence-transformers 向量化 — `/api/v1/embeddings`

本地 Embedding，无需调用云端 API。

```bash
# 批量向量化
curl -X POST http://localhost:8000/api/v1/embeddings/encode \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"texts":["第一段文本","第二段文本"],"normalize":true}'

# 相似度计算
curl -X POST http://localhost:8000/api/v1/embeddings/similarity \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text_a":"苹果是一种水果","text_b":"香蕉是热带水果"}'
```

默认模型：`paraphrase-multilingual-MiniLM-L12-v2`（多语言，适合中文）

---

### 12. whisperx 高精度转写 — `/api/v1/whisperx`

比 `/whisper` 更强：词级时间戳、可选说话人分离。

```bash
# 基础转写（含时间戳对齐）
curl -X POST "http://localhost:8000/api/v1/whisperx/transcribe?language=zh" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@meeting.wav"

# 启用说话人分离（需配置 WHISPERX_HF_TOKEN）
curl -X POST "http://localhost:8000/api/v1/whisperx/transcribe?enable_diarization=true&min_speakers=2&max_speakers=5" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@meeting.wav"
```

---

### 13. presidio PII 脱敏 — `/api/v1/presidio`

检测并脱敏手机号、邮箱、身份证等敏感信息。

```bash
# 检测 PII
curl -X POST http://localhost:8000/api/v1/presidio/analyze \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text":"请联系张三，手机13812345678，邮箱zhang@example.com","language":"zh"}'

# 自动脱敏
curl -X POST http://localhost:8000/api/v1/presidio/anonymize \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text":"请联系张三，手机13812345678"}'
```

---

### 14. Faster Whisper — `/api/v1/whisper`

轻量语音转文字，首次调用时加载模型。

```bash
curl -X POST "http://localhost:8000/api/v1/whisper/transcribe?language=zh" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@audio.wav"
```

---

### 15. Edge TTS — `/api/v1/edge-tts`

微软在线文字转语音，无需 API Key。

```bash
# 列出中文语音
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/edge-tts/voices?locale=zh-CN"

# 合成语音（返回 mp3）
curl -X POST http://localhost:8000/api/v1/edge-tts/synthesize \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text":"你好，欢迎使用 Pi Agent","voice":"zh-CN-XiaoxiaoNeural"}' \
  -o speech.mp3
```

---

### 16. LangExtract — `/api/v1/langextract`

LLM 结构化信息抽取，默认走 OpenAI 兼容网关（见 `.env` 中 `OPENAI_*`）。

```bash
curl -X POST http://localhost:8000/api/v1/langextract/extract \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "张三，手机13812345678，就职于北京某科技公司",
    "prompt_description": "提取人名、手机号、公司"
  }'
```

可视化：`POST /visualize` 返回 HTML 高亮页面。

---

### 17. 知识图谱 — `/api/v1/knowledge-graph`

按用户隔离的三元组存储，数据保存在 `.data/knowledge-graphs/`。

```bash
# 添加三元组
curl -X POST http://localhost:8000/api/v1/knowledge-graph/triples \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"subject":"Pi Agent","predicate":"是","obj":"智能体平台"}'

# 邻域查询
curl -X POST http://localhost:8000/api/v1/knowledge-graph/query \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"entity":"Pi Agent","depth":2}'
```

---

### 18. 媒体生成 — `/api/v1/media`

图片/视频生成，走 OpenAI 兼容网关（`.env` 中 `MEDIA_OPENAI_*` 或共用 `OPENAI_*`）。

```bash
curl -X POST http://localhost:8000/api/v1/media/image/generate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"一只在沙滩上的猫","size":"1024x1024"}'
```

---

### 19. Gemini 生图 — `/api/v1/gemini-image`

通过 Gemini 网页端 Cookie 生图（依赖 `gemini-webapi`）。

**配置（`.env`）：**

```env
GEMINI_SECURE_1PSID=        # 必填，浏览器 Cookie __Secure-1PSID 完整值
GEMINI_SECURE_1PSIDTS=      # 可选，部分账号已无此 Cookie
# GEMINI_PROXY=             # 可选代理；留空则不走代理
GEMINI_IMAGE_DIR=.data/gemini-images
```

```bash
# 检查状态（UNAUTHENTICATED 表示 Cookie 过期）
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/gemini-image/status

# 生图（storage_mode: disk / memory / both）
curl -X POST http://localhost:8000/api/v1/gemini-image/generate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"一只可爱的柴犬","storage_mode":"both"}'

# 更新 Cookie 后热重载（无需重启）
curl -X POST http://localhost:8000/api/v1/gemini-image/reload \
  -H "Authorization: Bearer $TOKEN"
```

---

### 20. 第三方集成 — `/api/v1/integrations/*`

| 路径 | 环境变量 | 说明 |
|------|---------|------|
| `/integrations/feishu` | `FEISHU_APP_ID`、`FEISHU_APP_SECRET` | 飞书消息推送 |
| `/integrations/wecom` | `WECOM_CORP_ID`、`WECOM_AGENT_ID`、`WECOM_SECRET` | 企业微信 |
| `/integrations/coze` | `COZE_API_BASE`、`COZE_API_TOKEN` | Coze Studio |
| `/integrations/n8n` | `N8N_WEBHOOK_BASE`、`N8N_API_KEY` | n8n Webhook |

```bash
# 飞书发文本消息示例
curl -X POST http://localhost:8000/api/v1/integrations/feishu/messages/text \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"receive_id":"ou_xxx","receive_id_type":"open_id","text":"Hello from Pi Agent"}'
```

各集成均有 `GET /status` 返回 `configured` 状态。

---

## 从 pi-agent 调用

```typescript
const { data: { session } } = await supabase.auth.getSession();

// OCR 示例
const form = new FormData();
form.append("file", imageFile);
await fetch("http://localhost:8000/api/v1/ocr/recognize", {
  method: "POST",
  headers: { Authorization: `Bearer ${session?.access_token}` },
  body: form,
});

// 中文分词示例
await fetch("http://localhost:8000/api/v1/nlp/segment", {
  method: "POST",
  headers: {
    Authorization: `Bearer ${session?.access_token}`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({ text: "待分词文本", engine: "jieba" }),
});
```

---

## 推荐处理流水线

```
网页内容
  → Playwright 抓取 HTML
  → trafilatura 抽正文
  → presidio 脱敏（可选）
  → sentence-transformers 本地向量化
  → pi-agent 知识库

附件文档
  → unstructured 统一解析
  → PyMuPDF / pdfplumber 补表格
  → PaddleOCR 补扫描件
  → jieba 分词
  → embeddings 向量化

视频 URL
  → yt-dlp 下载
  → scenedetect 分镜
  → whisperx 转写（说话人分离）
  → demucs 分离人声（可选）
```

---

## 系统依赖汇总


| 工具          | 用途                | 安装                            |
| ----------- | ----------------- | ----------------------------- |
| ffmpeg      | 转码、yt-dlp 合并、视频处理 | `brew install ffmpeg`         |
| ghostscript | camelot 表格提取      | `brew install ghostscript`    |
| Chromium    | Playwright（可选）    | `playwright install chromium`，且 `PLAYWRIGHT_ENABLED=true` |
---

## 环境变量

详见 `[.env.example](.env.example)`。核心配置：

```env
# Supabase（与 pi-agent 共用）
NEXT_PUBLIC_SUPABASE_URL=...
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=...
SUPABASE_SERVICE_ROLE_KEY=...

# 文档
DOCS_ENABLED=true

# Playwright（低内存服务器保持 false）
PLAYWRIGHT_ENABLED=false

# Whisper / Edge TTS
WHISPER_MODEL_SIZE=base
EDGE_TTS_DEFAULT_VOICE=zh-CN-XiaoxiaoNeural

# LangExtract / 媒体生成（OpenAI 兼容网关）
OPENAI_BASE_URL=https://api-inference.modelscope.cn/v1
OPENAI_API_KEY=ms-...
LANGEXTRACT_DEFAULT_MODEL=Qwen/Qwen3-235B-A22B

# ML / Top5 模块
PADDLEOCR_LANG=ch
EMBEDDING_MODEL_NAME=paraphrase-multilingual-MiniLM-L12-v2
WHISPERX_MODEL=base
WHISPERX_HF_TOKEN=          # 说话人分离
PRESIDIO_LANGUAGE=zh
VIDEO_WORK_DIR=.data/video-work
AUDIO_WORK_DIR=.data/audio-work
KNOWLEDGE_GRAPH_DIR=.data/knowledge-graphs

# Gemini 生图
GEMINI_SECURE_1PSID=
# GEMINI_SECURE_1PSIDTS=
# GEMINI_IMAGE_DIR=.data/gemini-images

# 第三方集成（按需）
# FEISHU_APP_ID= / WECOM_CORP_ID= / COZE_API_TOKEN= / N8N_WEBHOOK_BASE=
```

