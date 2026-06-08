import asyncio
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from app.config import get_settings


class FfmpegError(RuntimeError):
    pass


def _resolve_binary(name: str, configured: str | None) -> str | None:
    if configured:
        path = Path(configured)
        if path.exists():
            return str(path)
    return shutil.which(name)


def ffmpeg_path() -> str | None:
    settings = get_settings()
    return _resolve_binary("ffmpeg", settings.ffmpeg_path)


def ffprobe_path() -> str | None:
    settings = get_settings()
    return _resolve_binary("ffprobe", settings.ffprobe_path)


def status() -> dict[str, Any]:
    ff = ffmpeg_path()
    fp = ffprobe_path()
    return {
        "ffmpeg_available": ff is not None,
        "ffprobe_available": fp is not None,
        "ffmpeg_path": ff,
        "ffprobe_path": fp,
    }


def _run_command(args: list[str], timeout: int) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        raise FfmpegError(exc.stderr.strip() or exc.stdout.strip() or "ffmpeg 执行失败") from exc
    except subprocess.TimeoutExpired as exc:
        raise FfmpegError("ffmpeg 执行超时") from exc


def probe_media(file_path: Path) -> dict[str, Any]:
    ffprobe = ffprobe_path()
    if not ffprobe:
        raise FfmpegError("ffprobe 未安装，请安装 ffmpeg 或配置 FFMPEG_PATH")

    result = _run_command(
        [
            ffprobe,
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            str(file_path),
        ],
        timeout=get_settings().ffmpeg_timeout_sec,
    )
    return json.loads(result.stdout)


def transcode(
    input_path: Path,
    output_path: Path,
    *,
    output_format: str = "mp4",
    video_codec: str = "libx264",
    audio_codec: str = "aac",
    crf: int = 23,
) -> Path:
    ffmpeg = ffmpeg_path()
    if not ffmpeg:
        raise FfmpegError("ffmpeg 未安装，请安装 ffmpeg 或配置 FFMPEG_PATH")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    args = [
        ffmpeg,
        "-y",
        "-i",
        str(input_path),
        "-c:v",
        video_codec,
        "-c:a",
        audio_codec,
        "-crf",
        str(crf),
        str(output_path.with_suffix(f".{output_format}")),
    ]
    _run_command(args, timeout=get_settings().ffmpeg_timeout_sec)
    return output_path.with_suffix(f".{output_format}")


def extract_audio(
    input_path: Path,
    output_path: Path,
    *,
    audio_format: str = "mp3",
    audio_bitrate: str = "192k",
) -> Path:
    ffmpeg = ffmpeg_path()
    if not ffmpeg:
        raise FfmpegError("ffmpeg 未安装，请安装 ffmpeg 或配置 FFMPEG_PATH")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    out = output_path.with_suffix(f".{audio_format}")
    args = [
        ffmpeg,
        "-y",
        "-i",
        str(input_path),
        "-vn",
        "-acodec",
        "libmp3lame" if audio_format == "mp3" else "copy",
        "-b:a",
        audio_bitrate,
        str(out),
    ]
    _run_command(args, timeout=get_settings().ffmpeg_timeout_sec)
    return out


async def probe_media_async(file_path: Path) -> dict[str, Any]:
    return await asyncio.to_thread(probe_media, file_path)


async def transcode_async(
    input_path: Path,
    output_path: Path,
    **kwargs: Any,
) -> Path:
    return await asyncio.to_thread(transcode, input_path, output_path, **kwargs)


async def extract_audio_async(
    input_path: Path,
    output_path: Path,
    **kwargs: Any,
) -> Path:
    return await asyncio.to_thread(extract_audio, input_path, output_path, **kwargs)
