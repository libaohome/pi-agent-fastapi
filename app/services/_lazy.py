from typing import Any


def try_import(module: str, package: str | None = None) -> Any | None:
    try:
        return __import__(module, fromlist=[package] if package else [])
    except Exception:
        return None
