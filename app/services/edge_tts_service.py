from collections.abc import AsyncIterator

import edge_tts

from app.config import get_settings


async def list_voices(locale: str | None = None) -> list[dict]:
    voices = await edge_tts.list_voices()
    if locale:
        prefix = locale.lower()
        voices = [v for v in voices if v["Locale"].lower().startswith(prefix)]
    return [
        {
            "name": v["Name"],
            "short_name": v["ShortName"],
            "gender": v["Gender"],
            "locale": v["Locale"],
            "friendly_name": v["FriendlyName"],
        }
        for v in voices
    ]


def _resolve_voice(voice: str | None) -> str:
    if voice:
        return voice
    return get_settings().edge_tts_default_voice


async def synthesize_to_bytes(
    text: str,
    voice: str | None = None,
    rate: str = "+0%",
    volume: str = "+0%",
    pitch: str = "+0Hz",
) -> bytes:
    communicate = edge_tts.Communicate(
        text,
        _resolve_voice(voice),
        rate=rate,
        volume=volume,
        pitch=pitch,
    )
    chunks: list[bytes] = []
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            chunks.append(chunk["data"])
    return b"".join(chunks)


async def synthesize_stream(
    text: str,
    voice: str | None = None,
    rate: str = "+0%",
    volume: str = "+0%",
    pitch: str = "+0Hz",
) -> AsyncIterator[bytes]:
    communicate = edge_tts.Communicate(
        text,
        _resolve_voice(voice),
        rate=rate,
        volume=volume,
        pitch=pitch,
    )
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            yield chunk["data"]
