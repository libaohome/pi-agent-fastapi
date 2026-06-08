import asyncio
import subprocess
import sys
from pathlib import Path
from typing import Any

from app.config import get_settings
from app.services._lazy import try_import


def status() -> dict[str, Any]:
    return {
        "librosa": try_import("librosa") is not None,
        "pydub": try_import("pydub") is not None,
        "demucs": try_import("demucs") is not None,
    }


def analyze_librosa(file_path: Path) -> dict[str, Any]:
    librosa = try_import("librosa")
    if librosa is None:
        raise RuntimeError("librosa 未安装，请执行: pip install -e \".[ml]\"")
    y, sr = librosa.load(str(file_path), sr=None)
    duration = float(librosa.get_duration(y=y, sr=sr))
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    return {
        "sample_rate": int(sr),
        "duration_sec": duration,
        "channels": 1 if y.ndim == 1 else y.shape[0],
        "tempo_bpm": float(tempo) if tempo is not None else None,
        "rms": float(librosa.feature.rms(y=y).mean()),
    }


def slice_pydub(file_path: Path, start_ms: int, end_ms: int, output_path: Path, fmt: str = "mp3") -> Path:
    pydub = try_import("pydub")
    if pydub is None:
        raise RuntimeError("pydub 未安装，请执行: pip install -e \".[ml]\"")
    audio = pydub.AudioSegment.from_file(file_path)
    chunk = audio[start_ms:end_ms]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    chunk.export(output_path, format=fmt)
    return output_path


def convert_pydub(file_path: Path, output_path: Path, fmt: str = "wav", bitrate: str = "192k") -> Path:
    pydub = try_import("pydub")
    if pydub is None:
        raise RuntimeError("pydub 未安装，请执行: pip install -e \".[ml]\"")
    audio = pydub.AudioSegment.from_file(file_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    export_kwargs: dict[str, Any] = {"format": fmt}
    if fmt in {"mp3", "ogg"}:
        export_kwargs["bitrate"] = bitrate
    audio.export(output_path, **export_kwargs)
    return output_path


def separate_demucs(file_path: Path, user_id: str, stems: str = "vocals") -> dict[str, Any]:
    if try_import("demucs") is None:
        raise RuntimeError("demucs 未安装，请执行: pip install -e \".[ml]\"")
    settings = get_settings()
    out_dir = Path(settings.audio_work_dir) / user_id / file_path.stem
    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        "-m",
        "demucs",
        "-o",
        str(out_dir),
        "--two-stems",
        stems,
        str(file_path),
    ]
    subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=settings.demucs_timeout_sec)
    files = []
    for path in out_dir.rglob(f"*.{stems}.wav"):
        files.append(
            {
                "stem": stems,
                "name": path.name,
                "path": str(path),
                "size": path.stat().st_size,
            }
        )
    for path in out_dir.rglob("no_vocals.wav"):
        files.append({"stem": "no_vocals", "name": path.name, "path": str(path), "size": path.stat().st_size})
    return {"output_dir": str(out_dir), "files": files}


async def analyze_librosa_async(file_path: Path) -> dict[str, Any]:
    return await asyncio.to_thread(analyze_librosa, file_path)


async def slice_pydub_async(file_path: Path, start_ms: int, end_ms: int, output_path: Path, fmt: str = "mp3") -> Path:
    return await asyncio.to_thread(slice_pydub, file_path, start_ms, end_ms, output_path, fmt)


async def convert_pydub_async(file_path: Path, output_path: Path, fmt: str = "wav", bitrate: str = "192k") -> Path:
    return await asyncio.to_thread(convert_pydub, file_path, output_path, fmt, bitrate)


async def separate_demucs_async(file_path: Path, user_id: str, stems: str = "vocals") -> dict[str, Any]:
    return await asyncio.to_thread(separate_demucs, file_path, user_id, stems)
