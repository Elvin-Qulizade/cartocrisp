"""Minimal key -> localized string lookup for CLI and web messages."""
import json
from functools import lru_cache
from pathlib import Path

DEFAULT_LOCALE = "en"
SUPPORTED_LOCALES = ("az", "en", "tr", "ru")

_LOCALES_DIR = Path(__file__).parent / "locales"


@lru_cache(maxsize=None)
def _load(locale: str) -> dict:
    path = _LOCALES_DIR / f"{locale}.json"
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def translate(locale: str, key: str, **kwargs) -> str:
    strings = _load(locale) if locale in SUPPORTED_LOCALES else _load(DEFAULT_LOCALE)
    template = strings.get(key) or _load(DEFAULT_LOCALE).get(key, key)
    return template.format(**kwargs) if kwargs else template
