import asyncio
from pathlib import Path
from typing import Any

from app.services._lazy import try_import


def status() -> dict[str, Any]:
    return {
        "pymupdf": try_import("fitz") is not None,
        "pdfplumber": try_import("pdfplumber") is not None,
        "camelot": try_import("camelot") is not None,
    }


def extract_text_pymupdf(file_path: Path, page_start: int = 1, page_end: int | None = None) -> dict[str, Any]:
    fitz = try_import("fitz")
    if fitz is None:
        raise RuntimeError("PyMuPDF 未安装，请执行: pip install -e \".[ml]\"")
    doc = fitz.open(file_path)
    try:
        end = page_end or doc.page_count
        pages = []
        for i in range(page_start - 1, min(end, doc.page_count)):
            page = doc.load_page(i)
            pages.append({"page": i + 1, "text": page.get_text()})
        return {"page_count": doc.page_count, "pages": pages}
    finally:
        doc.close()


def extract_images_pymupdf(file_path: Path, page: int = 1) -> list[dict[str, Any]]:
    fitz = try_import("fitz")
    if fitz is None:
        raise RuntimeError("PyMuPDF 未安装，请执行: pip install -e \".[ml]\"")
    doc = fitz.open(file_path)
    try:
        pg = doc.load_page(page - 1)
        images = []
        for idx, img in enumerate(pg.get_images(full=True)):
            xref = img[0]
            base = doc.extract_image(xref)
            images.append(
                {
                    "index": idx,
                    "ext": base.get("ext"),
                    "width": base.get("width"),
                    "height": base.get("height"),
                    "image_base64": __import__("base64").b64encode(base["image"]).decode(),
                }
            )
        return images
    finally:
        doc.close()


def extract_tables_pdfplumber(file_path: Path, pages: str = "all") -> dict[str, Any]:
    pdfplumber = try_import("pdfplumber")
    if pdfplumber is None:
        raise RuntimeError("pdfplumber 未安装，请执行: pip install -e \".[ml]\"")
    tables_out: list[dict[str, Any]] = []
    with pdfplumber.open(file_path) as pdf:
        page_indexes = range(len(pdf.pages)) if pages == "all" else _parse_pages(pages, len(pdf.pages))
        for i in page_indexes:
            page = pdf.pages[i]
            for t_idx, table in enumerate(page.extract_tables() or []):
                tables_out.append({"page": i + 1, "table_index": t_idx, "rows": table})
    return {"table_count": len(tables_out), "tables": tables_out}


def extract_tables_camelot(file_path: Path, pages: str = "1", flavor: str = "lattice") -> dict[str, Any]:
    camelot = try_import("camelot")
    if camelot is None:
        raise RuntimeError("camelot 未安装，请执行: pip install -e \".[ml]\"（需系统 ghostscript）")
    tables = camelot.read_pdf(str(file_path), pages=pages, flavor=flavor)
    result = []
    for table in tables:
        result.append(
            {
                "page": table.page,
                "order": table.order,
                "accuracy": table.accuracy,
                "rows": table.data,
            }
        )
    return {"table_count": len(result), "tables": result}


def _parse_pages(pages: str, total: int) -> list[int]:
    indexes: list[int] = []
    for part in pages.split(","):
        part = part.strip()
        if "-" in part:
            start, end = part.split("-", 1)
            indexes.extend(range(int(start) - 1, min(int(end), total)))
        elif part.isdigit():
            indexes.append(int(part) - 1)
    return sorted(set(i for i in indexes if 0 <= i < total))


async def extract_text_pymupdf_async(file_path: Path, **kwargs: Any) -> dict[str, Any]:
    return await asyncio.to_thread(extract_text_pymupdf, file_path, **kwargs)


async def extract_images_pymupdf_async(file_path: Path, page: int = 1) -> list[dict[str, Any]]:
    return await asyncio.to_thread(extract_images_pymupdf, file_path, page)


async def extract_tables_pdfplumber_async(file_path: Path, pages: str = "all") -> dict[str, Any]:
    return await asyncio.to_thread(extract_tables_pdfplumber, file_path, pages)


async def extract_tables_camelot_async(file_path: Path, pages: str = "1", flavor: str = "lattice") -> dict[str, Any]:
    return await asyncio.to_thread(extract_tables_camelot, file_path, pages, flavor)
