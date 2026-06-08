import asyncio
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import yt_dlp

from app.config import get_settings
from app.schemas.common import YtdlpDownloadRequest
from app.services.ffmpeg_service import ffmpeg_path
from app.services.playwright_sandbox import SandboxError, validate_target_url

_tasks: dict[str, dict[str, Any]] = {}


def _work_dir(user_id: str, task_id: str | None = None) -> Path:
    settings = get_settings()
    tid = task_id or str(uuid4())
    path = Path(settings.ytdlp_download_dir) / user_id / tid
    path.mkdir(parents=True, exist_ok=True)
    return path


def _base_opts(user_id: str, task_id: str | None = None) -> dict[str, Any]:
    settings = get_settings()
    out_dir = _work_dir(user_id, task_id)
    opts: dict[str, Any] = {
        "outtmpl": str(out_dir / "%(title).200B [%(id)s].%(ext)s"),
        "noplaylist": not settings.ytdlp_allow_playlist,
        "quiet": True,
        "no_warnings": True,
        "socket_timeout": settings.ytdlp_socket_timeout,
        "retries": settings.ytdlp_retries,
    }
    ff = ffmpeg_path()
    if ff:
        opts["ffmpeg_location"] = str(Path(ff).parent)
    if settings.ytdlp_proxy:
        opts["proxy"] = settings.ytdlp_proxy
    if settings.ytdlp_cookies_file:
        opts["cookiefile"] = settings.ytdlp_cookies_file
    return opts


def _serialize_info(info: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": info.get("id"),
        "title": info.get("title"),
        "description": info.get("description"),
        "uploader": info.get("uploader"),
        "duration": info.get("duration"),
        "view_count": info.get("view_count"),
        "webpage_url": info.get("webpage_url") or info.get("original_url"),
        "thumbnail": info.get("thumbnail"),
        "formats": [
            {
                "format_id": f.get("format_id"),
                "ext": f.get("ext"),
                "resolution": f.get("resolution"),
                "filesize": f.get("filesize"),
                "vcodec": f.get("vcodec"),
                "acodec": f.get("acodec"),
            }
            for f in (info.get("formats") or [])
            if f.get("format_id")
        ][-20:],
    }


def _pick_downloaded_files(directory: Path) -> list[dict[str, Any]]:
    files = []
    for path in sorted(directory.iterdir()):
        if path.is_file():
            files.append(
                {
                    "name": path.name,
                    "path": str(path),
                    "size": path.stat().st_size,
                    "ext": path.suffix.lstrip("."),
                }
            )
    return files


def _extract_info(url: str, opts: dict[str, Any]) -> dict[str, Any]:
    with yt_dlp.YoutubeDL(opts) as ydl:
        return ydl.extract_info(url, download=False)


def _download(url: str, opts: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
    out_dir = Path(opts["outtmpl"]).parent
    return _serialize_info(info), _pick_downloaded_files(out_dir)


def status() -> dict[str, Any]:
    settings = get_settings()
    return {
        "ytdlp_version": yt_dlp.version.__version__,
        "ffmpeg_available": ffmpeg_path() is not None,
        "ffmpeg_path": ffmpeg_path(),
        "download_dir": settings.ytdlp_download_dir,
        "allow_playlist": settings.ytdlp_allow_playlist,
    }


def get_video_info(url: str) -> dict[str, Any]:
    validate_target_url(url)
    opts = _base_opts("_probe")
    return _extract_info(url, opts)


def download_video(user_id: str, request: YtdlpDownloadRequest) -> dict[str, Any]:
    validate_target_url(request.url)
    task_id = str(uuid4())
    opts = _base_opts(user_id, task_id)

    if request.audio_only:
        opts["format"] = "bestaudio/best"
        opts["postprocessors"] = [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": request.audio_format,
                "preferredquality": request.audio_quality,
            }
        ]
    elif request.format:
        opts["format"] = request.format
    else:
        opts["format"] = "bestvideo*+bestaudio/best"

    if request.subtitles:
        opts["writesubtitles"] = True
        opts["writeautomaticsub"] = True
        opts["subtitleslangs"] = request.subtitle_langs

    if request.max_filesize_mb:
        opts["max_filesize"] = request.max_filesize_mb * 1024 * 1024

    info, files = _download(request.url, opts)

    return {
        "task_id": task_id,
        "info": info,
        "files": files,
    }


def _create_task(user_id: str, payload: dict) -> str:
    task_id = str(uuid4())
    _tasks[task_id] = {
        "id": task_id,
        "user_id": user_id,
        "status": "pending",
        "payload": payload,
        "result": None,
        "error": None,
        "created_at": datetime.now(UTC).isoformat(),
        "completed_at": None,
    }
    return task_id


async def _run_background_task(task_id: str) -> None:
    task = _tasks.get(task_id)
    if not task:
        return
    task["status"] = "running"
    try:
        request = YtdlpDownloadRequest(**task["payload"])
        result = await asyncio.to_thread(download_video, task["user_id"], request)
        task["result"] = result
        task["status"] = "completed"
    except (SandboxError, ValueError) as exc:
        task["status"] = "failed"
        task["error"] = str(exc)
    except Exception as exc:
        task["status"] = "failed"
        task["error"] = f"下载失败: {exc}"
    finally:
        task["completed_at"] = datetime.now(UTC).isoformat()


def submit_background_task(user_id: str, payload: dict) -> str:
    task_id = _create_task(user_id, payload)
    asyncio.create_task(_run_background_task(task_id))
    return task_id


def get_task(task_id: str, user_id: str) -> dict[str, Any] | None:
    task = _tasks.get(task_id)
    if not task or task["user_id"] != user_id:
        return None
    return task


def resolve_task_file(task_id: str, user_id: str, filename: str | None = None) -> Path | None:
    task = get_task(task_id, user_id)
    if not task or task["status"] != "completed":
        return None
    files = (task.get("result") or {}).get("files") or []
    if not files:
        return None
    if filename:
        for item in files:
            if item["name"] == filename:
                return Path(item["path"])
        return None
    return Path(files[0]["path"])
