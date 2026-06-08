from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.api._upload import save_upload
from app.core.auth import AuthContext, get_current_user
from app.services import pdf_service as pdf

router = APIRouter(prefix="/pdf", tags=["pdf"])


@router.get("/status")
async def pdf_status(_: Annotated[AuthContext, Depends(get_current_user)]):
    return pdf.status()


@router.post("/pymupdf/text")
async def pymupdf_text(
    file: Annotated[UploadFile, File(...)],
    _: Annotated[AuthContext, Depends(get_current_user)],
    page_start: Annotated[int, Form(ge=1)] = 1,
    page_end: Annotated[int | None, Form()] = None,
):
    tmp_path = await save_upload(file, ".pdf")
    try:
        result = await pdf.extract_text_pymupdf_async(tmp_path, page_start=page_start, page_end=page_end)
    except RuntimeError as exc:
        raise HTTPException(503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(500, detail=f"PyMuPDF 提取失败: {exc}") from exc
    finally:
        tmp_path.unlink(missing_ok=True)
    return result


@router.post("/pymupdf/images")
async def pymupdf_images(
    file: Annotated[UploadFile, File(...)],
    _: Annotated[AuthContext, Depends(get_current_user)],
    page: Annotated[int, Form(ge=1)] = 1,
):
    tmp_path = await save_upload(file, ".pdf")
    try:
        result = await pdf.extract_images_pymupdf_async(tmp_path, page=page)
    except RuntimeError as exc:
        raise HTTPException(503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(500, detail=f"PyMuPDF 图片提取失败: {exc}") from exc
    finally:
        tmp_path.unlink(missing_ok=True)
    return {"images": result}


@router.post("/pdfplumber/tables")
async def pdfplumber_tables(
    file: Annotated[UploadFile, File(...)],
    _: Annotated[AuthContext, Depends(get_current_user)],
    pages: Annotated[str, Form()] = "all",
):
    tmp_path = await save_upload(file, ".pdf")
    try:
        result = await pdf.extract_tables_pdfplumber_async(tmp_path, pages=pages)
    except RuntimeError as exc:
        raise HTTPException(503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(500, detail=f"pdfplumber 表格提取失败: {exc}") from exc
    finally:
        tmp_path.unlink(missing_ok=True)
    return result


@router.post("/camelot/tables")
async def camelot_tables(
    file: Annotated[UploadFile, File(...)],
    _: Annotated[AuthContext, Depends(get_current_user)],
    pages: Annotated[str, Form()] = "1",
    flavor: Annotated[str, Form()] = "lattice",
):
    tmp_path = await save_upload(file, ".pdf")
    try:
        result = await pdf.extract_tables_camelot_async(tmp_path, pages=pages, flavor=flavor)
    except RuntimeError as exc:
        raise HTTPException(503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(500, detail=f"camelot 表格提取失败: {exc}") from exc
    finally:
        tmp_path.unlink(missing_ok=True)
    return result
