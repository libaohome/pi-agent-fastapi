import tempfile
from pathlib import Path

from fastapi import UploadFile


async def save_upload(file: UploadFile, suffix: str | None = None) -> Path:
    ext = suffix or Path(file.filename or "upload.bin").suffix or ".bin"
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp.write(await file.read())
        return Path(tmp.name)
