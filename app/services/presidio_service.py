import asyncio
from functools import lru_cache
from typing import Any

from app.config import get_settings
from app.services._lazy import try_import


@lru_cache
def _get_analyzer():
    analyzer_mod = try_import("presidio_analyzer")
    if analyzer_mod is None:
        raise RuntimeError("presidio 未安装，请执行: pip install -e \".[ml,top5]\"")
    return analyzer_mod.AnalyzerEngine()


@lru_cache
def _get_anonymizer():
    anonymizer_mod = try_import("presidio_anonymizer")
    if anonymizer_mod is None:
        raise RuntimeError("presidio 未安装，请执行: pip install -e \".[ml,top5]\"")
    return anonymizer_mod.AnonymizerEngine()


def status() -> dict[str, Any]:
    settings = get_settings()
    return {
        "available": try_import("presidio_analyzer") is not None
        and try_import("presidio_anonymizer") is not None,
        "default_language": settings.presidio_language,
    }


def analyze_text(text: str, language: str | None = None) -> dict[str, Any]:
    analyzer = _get_analyzer()
    lang = language or get_settings().presidio_language
    results = analyzer.analyze(text=text, language=lang)
    entities = [
        {
            "type": r.entity_type,
            "start": r.start,
            "end": r.end,
            "score": r.score,
            "text": text[r.start : r.end],
        }
        for r in results
    ]
    return {"language": lang, "entity_count": len(entities), "entities": entities}


def anonymize_text(text: str, language: str | None = None) -> dict[str, Any]:
    anonymizer_entities = try_import("presidio_anonymizer.entities")
    if anonymizer_entities is None:
        raise RuntimeError("presidio 未安装，请执行: pip install -e \".[ml,top5]\"")
    OperatorConfig = anonymizer_entities.OperatorConfig

    analyzer = _get_analyzer()
    anonymizer = _get_anonymizer()
    lang = language or get_settings().presidio_language
    results = analyzer.analyze(text=text, language=lang)
    anonymized = anonymizer.anonymize(
        text=text,
        analyzer_results=results,
        operators={"DEFAULT": OperatorConfig("replace", {"new_value": "<REDACTED>"})},
    )
    return {
        "language": lang,
        "original_length": len(text),
        "text": anonymized.text,
        "items": [
            {
                "type": item.entity_type,
                "start": item.start,
                "end": item.end,
                "operator": item.operator,
            }
            for item in anonymized.items
        ],
    }


async def analyze_text_async(text: str, language: str | None = None) -> dict[str, Any]:
    return await asyncio.to_thread(analyze_text, text, language)


async def anonymize_text_async(text: str, language: str | None = None) -> dict[str, Any]:
    return await asyncio.to_thread(anonymize_text, text, language)
