from fastapi import APIRouter

from app.api import (
    audio_tools,
    document,
    edge_tts,
    embeddings,
    extract_web,
    ffmpeg,
    image_tools,
    knowledge_graph,
    langextract,
    markitdown,
    media,
    nlp,
    ocr,
    pdf_tools,
    playwright,
    presidio,
    video_tools,
    whisper,
    whisperx,
    ytdlp,
)
from app.api.integrations import coze, feishu, n8n, wecom

api_router = APIRouter()
api_router.include_router(markitdown.router)
api_router.include_router(whisper.router)
api_router.include_router(edge_tts.router)
api_router.include_router(langextract.router)
api_router.include_router(playwright.router)
api_router.include_router(ytdlp.router)
api_router.include_router(ffmpeg.router)
api_router.include_router(ocr.router)
api_router.include_router(image_tools.router)
api_router.include_router(pdf_tools.router)
api_router.include_router(video_tools.router)
api_router.include_router(audio_tools.router)
api_router.include_router(nlp.router)
api_router.include_router(extract_web.router)
api_router.include_router(document.router)
api_router.include_router(embeddings.router)
api_router.include_router(whisperx.router)
api_router.include_router(presidio.router)
api_router.include_router(knowledge_graph.router)
api_router.include_router(feishu.router)
api_router.include_router(wecom.router)
api_router.include_router(coze.router)
api_router.include_router(n8n.router)
api_router.include_router(media.router)
