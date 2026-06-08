import asyncio
import tempfile
from pathlib import Path
from typing import Any

import langextract as lx
from langextract.factory import ModelConfig

from app.config import get_settings
from app.schemas.common import LangExtractExample, LangExtractRequest


def _build_examples(examples: list[LangExtractExample]) -> list[lx.data.ExampleData]:
    return [
        lx.data.ExampleData(
            text=example.text,
            extractions=[
                lx.data.Extraction(
                    extraction_class=item.extraction_class,
                    extraction_text=item.extraction_text,
                    attributes=item.attributes,
                )
                for item in example.extractions
            ],
        )
        for example in examples
    ]


def _serialize_extraction(extraction: lx.data.Extraction) -> dict[str, Any]:
    data: dict[str, Any] = {
        "extraction_class": extraction.extraction_class,
        "extraction_text": extraction.extraction_text,
        "attributes": extraction.attributes or {},
    }
    if extraction.char_interval is not None:
        data["char_interval"] = {
            "start_pos": extraction.char_interval.start_pos,
            "end_pos": extraction.char_interval.end_pos,
        }
    if extraction.alignment_status is not None:
        data["alignment_status"] = str(extraction.alignment_status)
    if extraction.extraction_index is not None:
        data["extraction_index"] = extraction.extraction_index
    return data


def _serialize_result(result: Any) -> dict[str, Any]:
    extractions = [_serialize_extraction(e) for e in result.extractions]
    grounded = [e for e in extractions if e.get("char_interval")]
    return {
        "text": getattr(result, "text", None),
        "extractions": extractions,
        "grounded_count": len(grounded),
        "total_count": len(extractions),
    }


def _build_extract_kwargs(request: LangExtractRequest) -> dict[str, Any]:
    settings = get_settings()
    text_or_documents = request.text or request.url
    if not text_or_documents:
        raise ValueError("text 或 url 至少提供一个")

    kwargs: dict[str, Any] = {
        "text_or_documents": text_or_documents,
        "prompt_description": request.prompt_description,
        "examples": _build_examples(request.examples),
        "extraction_passes": request.extraction_passes,
        "max_workers": request.max_workers,
        "max_char_buffer": request.max_char_buffer,
    }

    if request.language_model_params:
        kwargs["language_model_params"] = request.language_model_params

    provider = request.provider or settings.langextract_default_provider
    model_id = request.model_id or settings.langextract_default_model

    if provider == "openai":
        api_key = settings.langextract_openai_api_key
        base_url = settings.langextract_openai_base_url
        if not api_key:
            raise RuntimeError("OpenAI 兼容模式未配置 OPENAI_API_KEY / LANGEXTRACT_OPENAI_API_KEY")
        provider_kwargs: dict[str, Any] = {"api_key": api_key}
        if base_url:
            provider_kwargs["base_url"] = base_url.rstrip("/")
        kwargs["config"] = ModelConfig(
            model_id=model_id,
            provider="openai",
            provider_kwargs=provider_kwargs,
        )
    elif provider == "ollama":
        kwargs["model_id"] = model_id
        if request.model_url or settings.langextract_ollama_url:
            kwargs["model_url"] = request.model_url or settings.langextract_ollama_url
    else:
        kwargs["model_id"] = model_id
        api_key = settings.langextract_api_key
        if api_key:
            kwargs["api_key"] = api_key

    return kwargs


def _run_extract(request: LangExtractRequest) -> dict[str, Any]:
    result = lx.extract(**_build_extract_kwargs(request))
    return _serialize_result(result)


def _run_extract_with_visualization(request: LangExtractRequest) -> tuple[dict[str, Any], str]:
    kwargs = _build_extract_kwargs(request)
    result = lx.extract(**kwargs)
    serialized = _serialize_result(result)

    with tempfile.TemporaryDirectory() as tmp_dir:
        output_dir = Path(tmp_dir)
        lx.io.save_annotated_documents(
            [result],
            output_name="extraction_results.jsonl",
            output_dir=str(output_dir),
        )
        jsonl_path = output_dir / "extraction_results.jsonl"
        html_content = lx.visualize(str(jsonl_path))
        if hasattr(html_content, "data"):
            html = html_content.data
        else:
            html = str(html_content)

    return serialized, html


async def extract_structured(request: LangExtractRequest) -> dict[str, Any]:
    return await asyncio.to_thread(_run_extract, request)


async def extract_with_visualization(request: LangExtractRequest) -> tuple[dict[str, Any], str]:
    return await asyncio.to_thread(_run_extract_with_visualization, request)
