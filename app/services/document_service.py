import asyncio
from pathlib import Path
from typing import Any

from app.services._lazy import try_import


def status() -> dict[str, Any]:
    return {"available": try_import("unstructured") is not None}


def _element_to_dict(element: Any) -> dict[str, Any]:
    return {
        "type": type(element).__name__,
        "text": str(element),
        "metadata": dict(element.metadata.to_dict()) if hasattr(element, "metadata") else {},
    }


def parse_document(file_path: Path, strategy: str = "auto") -> dict[str, Any]:
    if try_import("unstructured") is None:
        raise RuntimeError("unstructured 未安装，请执行: pip install -e \".[ml,top5]\"")

    suffix = file_path.suffix.lower()
    elements: list[Any] = []

    if suffix == ".pdf":
        from unstructured.partition.pdf import partition_pdf

        elements = partition_pdf(str(file_path), strategy=strategy)
    elif suffix in {".docx", ".doc"}:
        from unstructured.partition.docx import partition_docx

        elements = partition_docx(str(file_path))
    elif suffix in {".pptx", ".ppt"}:
        from unstructured.partition.pptx import partition_pptx

        elements = partition_pptx(str(file_path))
    elif suffix in {".xlsx", ".xls"}:
        from unstructured.partition.xlsx import partition_xlsx

        elements = partition_xlsx(str(file_path))
    elif suffix in {".html", ".htm"}:
        from unstructured.partition.html import partition_html

        elements = partition_html(str(file_path))
    elif suffix == ".md":
        from unstructured.partition.md import partition_md

        elements = partition_md(str(file_path))
    elif suffix == ".csv":
        from unstructured.partition.csv import partition_csv

        elements = partition_csv(str(file_path))
    elif suffix == ".eml":
        from unstructured.partition.email import partition_email

        elements = partition_email(str(file_path))
    else:
        from unstructured.partition.auto import partition

        elements = partition(filename=str(file_path))

    items = [_element_to_dict(el) for el in elements]
    full_text = "\n\n".join(item["text"] for item in items if item["text"])
    return {
        "filename": file_path.name,
        "element_count": len(items),
        "text": full_text,
        "elements": items,
    }


async def parse_document_async(file_path: Path, strategy: str = "auto") -> dict[str, Any]:
    return await asyncio.to_thread(parse_document, file_path, strategy)
