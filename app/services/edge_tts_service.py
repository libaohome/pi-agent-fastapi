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


def resolve_voice(voice: str | None) -> str:
    if voice:
        return voice
    return get_settings().edge_tts_default_voice


class SynthesisError(RuntimeError):
    pass


async def synthesize_to_bytes(
    text: str,
    voice: str | None = None,
    rate: str = "+0%",
    volume: str = "+0%",
    pitch: str = "+0Hz",
) -> bytes:
    resolved_voice = resolve_voice(voice)
    communicate = edge_tts.Communicate(
        text,
        resolved_voice,
        rate=rate,
        volume=volume,
        pitch=pitch,
    )
    chunks: list[bytes] = []
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            chunks.append(chunk["data"])
    audio = b"".join(chunks)
    if not audio:
        raise SynthesisError(f"语音合成未返回音频数据（voice={resolved_voice}）")
    return audio


async def synthesize_stream(
    text: str,
    voice: str | None = None,
    rate: str = "+0%",
    volume: str = "+0%",
    pitch: str = "+0Hz",
) -> AsyncIterator[bytes]:
    communicate = edge_tts.Communicate(
        text,
        resolve_voice(voice),
        rate=rate,
        volume=volume,
        pitch=pitch,
    )
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            yield chunk["data"]
