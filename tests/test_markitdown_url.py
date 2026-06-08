import pytest

from app.services.markitdown_service import ConvertResult, UrlConvertError, convert_file


def test_convert_file_raises_on_empty(tmp_path):
    empty = tmp_path / "empty.txt"
    empty.write_text("   ")
    with pytest.raises(UrlConvertError, match="未能从文件中提取"):
        convert_file(empty)


@pytest.mark.asyncio
async def test_download_and_convert(monkeypatch):
    monkeypatch.setattr(
        "app.services.markitdown_service.validate_target_url",
        lambda url: None,
    )
    async def fake_download(url, timeout=60):
        return "<html><body><h1>hi</h1></body></html>"

    monkeypatch.setattr(
        "app.services.markitdown_service.download_html_async",
        fake_download,
    )
    monkeypatch.setattr(
        "app.services.markitdown_service._convert_html_bytes",
        lambda content, suffix=".html": ConvertResult(
            content="# hi",
            method="markitdown_download",
            format="markdown",
        ),
    )

    from app.services.markitdown_service import download_and_convert

    result = await download_and_convert("https://example.com/page")
    assert result.format == "markdown"
    assert result.content == "# hi"
