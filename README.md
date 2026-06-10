# Pi Agent FastAPI

Pi Agent 的 Python 侧服务，与 `[../pi-agent](../pi-agent)`（Next.js）共用 **Supabase 项目** 与 **鉴权 Token**。

## 职责总览


| 模块                                 | 路径                        | 说明                                |
| ---------------------------------- | ------------------------- | --------------------------------- |
| MarkItDown                         | `/api/v1/markitdown`      | 文档/网页转 Markdown                   |
| Faster Whisper                     | `/api/v1/whisper`         | 语音转文字                             |
| Edge TTS                           | `/api/v1/edge-tts`        | 文字转语音                             |
| LangExtract                        | `/api/v1/langextract`     | LLM 结构化信息抽取                       |
| Playwright                         | `/api/v1/playwright`      | 后台无头沙箱浏览器                         |
| yt-dlp                             | `/api/v1/ytdlp`           | 视频/音频下载                           |
| ffmpeg                             | `/api/v1/ffmpeg`          | 媒体探测、转码、提取音频                      |
| **PaddleOCR**                      | `/api/v1/ocr`             | 图片/PDF 扫描件 OCR                    |
| **rembg**                          | `/api/v1/image`           | 图片抠图去背景                           |
| **PyMuPDF / pdfplumber / camelot** | `/api/v1/pdf`             | PDF 文本/图片/表格提取                    |
| **moviepy / scenedetect**          | `/api/v1/video-tools`     | 视频裁剪、分镜、缩略图                       |
| **librosa / pydub / demucs**       | `/api/v1/audio-tools`     | 音频分析、切片、音轨分离                      |
| **jieba**                          | `/api/v1/nlp`             | 中文分词与关键词（pkuseg 不支持 Py3.12，见下方说明） |
| **trafilatura**                    | `/api/v1/extract-web`     | 网页正文抽取（配合 Playwright）             |
| **unstructured**                   | `/api/v1/document`        | 统一文档解析（PDF/Word/PPT/邮件等）          |
| **sentence-transformers**          | `/api/v1/embeddings`      | 本地文本向量化与相似度                       |
| **whisperx**                       | `/api/v1/whisperx`        | 高精度转写 + 时间戳 + 说话人分离               |
| **presidio**                       | `/api/v1/presidio`        | PII 检测与脱敏                         |
| 知识图谱                               | `/api/v1/knowledge-graph` | 三元组存储与邻域查询                        |
| 飞书 / 企微 / Coze / n8n               | `/api/v1/integrations/`*  | 第三方集成                             |
| 媒体生成                               | `/api/v1/media`           | 图片/视频（OpenAI 兼容网关）                |


> 加粗模块需安装扩展依赖：`pip install -e ".[dev,ml,top5]"`

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

```bash
cd pi-agent-fastapi
cp .env.example .env
# 填入与 pi-agent 相同的 Supabase 配置

## mac下安装ffmpeg
brew install ffmpeg
conda install ffmpeg
## ubuntu下安装ffmpeg
sudo apt update
sudo apt install -y ffmpeg
## centos下安装ffmpeg
sudo yum install -y epel-release
sudo yum install -y ffmpeg
sudo dnf install -y ffmpeg
## fedro下安装ffmpeg
sudo dnf install -y ffmpeg
## 安装结果确认
which ffmpeg
ffmpeg -version

#创建虚拟运行环境（开发阶段）
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,ml,top5]"   # 含 OCR/PDF/音视频/NLP/Top5 等扩展库

# 或使用脚本：bash scripts/install-ml.sh

python -m spacy download zh_core_web_sm   # presidio 中文支持（可选）

playwright install chromium   # Playwright 需要
# 系统依赖
# macOS:  brew install ffmpeg ghostscript
# Ubuntu: apt install ffmpeg ghostscript

uvicorn app.main:app --reload --port 8000

#生产环境部署命令
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
```

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

- 按模块 **Tag 分组**（OCR、PDF、音视频、集成等）
- **持久化鉴权**（刷新页面 Token 仍保留）
- 接口 **耗时显示**、关键字 **过滤搜索**
- 生产环境可通过 `DOCS_ENABLED=false` 关闭

### 依赖分组说明


| 安装命令                              | 包含能力                                                       |
| --------------------------------- | ---------------------------------------------------------- |
| `pip install -e ".[dev]"`         | 基础服务（markitdown、whisper、playwright 等）                      |
| `pip install -e ".[dev,ml]"`      | OCR、PDF、rembg、音视频处理、NLP                                    |
| `pip install -e ".[dev,ml,top5]"` | 额外启用 trafilatura、unstructured、embeddings、whisperx、presidio |


各模块 `GET /status` 会返回对应库是否可用。

---

## 使用手册

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

```bash
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
| Chromium    | Playwright        | `playwright install chromium` |


---

## 环境变量

详见 `[.env.example](.env.example)`。核心配置：

```env
NEXT_PUBLIC_SUPABASE_URL=...
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=...
SUPABASE_SERVICE_ROLE_KEY=...

# ML / Top5 模块
PADDLEOCR_LANG=ch
EMBEDDING_MODEL_NAME=paraphrase-multilingual-MiniLM-L12-v2
WHISPERX_MODEL=base
WHISPERX_HF_TOKEN=          # 说话人分离
PRESIDIO_LANGUAGE=zh
VIDEO_WORK_DIR=.data/video-work
AUDIO_WORK_DIR=.data/audio-work
```

