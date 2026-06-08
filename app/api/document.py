from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.api._upload import save_upload
from app.core.auth import AuthContext, get_current_user
from app.services import document_service as doc

router = APIRouter(prefix="/document", tags=["document"])


@router.get("/status")
async def document_status(_: Annotated[AuthContext, Depends(get_current_user)]):
    return doc.status()


@router.post("/parse")
async def parse_document(
    file: Annotated[UploadFile, File(...)],
    _: Annotated[AuthContext, Depends(get_current_user)],
    strategy: Annotated[str, Form()] = "auto",
):
    tmp_path = await save_upload(file)
    try:
        result = await doc.parse_document_async(tmp_path, strategy=strategy)
    except RuntimeError as exc:
        raise HTTPException(503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(500, detail=f"文档解析失败: {exc}") from exc
    finally:
        tmp_path.unlink(missing_ok=True)
    return result
