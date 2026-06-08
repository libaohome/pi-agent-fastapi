import asyncio
import base64
from pathlib import Path
from typing import Any

from app.config import get_settings
from app.services._lazy import try_import


def status() -> dict[str, Any]:
    return {
        "moviepy": try_import("moviepy") is not None,
        "scenedetect": try_import("scenedetect") is not None,
    }


def detect_scenes(file_path: Path, threshold: float = 27.0) -> dict[str, Any]:
    scenedetect = try_import("scenedetect")
    if scenedetect is None:
        raise RuntimeError("scenedetect 未安装，请执行: pip install -e \".[ml]\"")
    from scenedetect import ContentDetector, detect

    scene_list = detect(str(file_path), ContentDetector(threshold=threshold))
    scenes = []
    for idx, (start, end) in enumerate(scene_list):
        scenes.append(
            {
                "index": idx,
                "start_sec": start.get_seconds(),
                "end_sec": end.get_seconds(),
                "start_timecode": start.get_timecode(),
                "end_timecode": end.get_timecode(),
            }
        )
    return {"scene_count": len(scenes), "scenes": scenes}


def clip_video(file_path: Path, start_sec: float, end_sec: float, output_path: Path) -> Path:
    moviepy = try_import("moviepy")
    if moviepy is None:
        raise RuntimeError("moviepy 未安装，请执行: pip install -e \".[ml]\"")
    from moviepy import VideoFileClip

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with VideoFileClip(str(file_path)) as clip:
        sub = clip.subclipped(start_sec, end_sec)
        sub.write_videofile(str(output_path), logger=None)
    return output_path


def extract_thumbnail(file_path: Path, at_sec: float = 0.0) -> bytes:
    moviepy = try_import("moviepy")
    if moviepy is None:
        raise RuntimeError("moviepy 未安装，请执行: pip install -e \".[ml]\"")
    from moviepy import VideoFileClip

    with VideoFileClip(str(file_path)) as clip:
        frame = clip.get_frame(at_sec)
    from PIL import Image
    import io

    img = Image.fromarray(frame)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def thumbnail_base64(file_path: Path, at_sec: float = 0.0) -> str:
    return base64.b64encode(extract_thumbnail(file_path, at_sec)).decode()


def save_work_copy(user_id: str, file_path: Path) -> Path:
    settings = get_settings()
    out_dir = Path(settings.video_work_dir) / user_id
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / file_path.name
    if file_path != target:
        target.write_bytes(file_path.read_bytes())
    return target


async def detect_scenes_async(file_path: Path, threshold: float = 27.0) -> dict[str, Any]:
    return await asyncio.to_thread(detect_scenes, file_path, threshold)


async def clip_video_async(file_path: Path, start_sec: float, end_sec: float, output_path: Path) -> Path:
    return await asyncio.to_thread(clip_video, file_path, start_sec, end_sec, output_path)


async def thumbnail_base64_async(file_path: Path, at_sec: float = 0.0) -> str:
    return await asyncio.to_thread(thumbnail_base64, file_path, at_sec)
