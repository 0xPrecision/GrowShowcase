from pathlib import Path
from contextlib import contextmanager
from typing import Optional

from services.i18n.translations import (
    Translator,
    set_current_locale,
    reset_current_locale,
)

# Один общий Translator на всё приложение
translator = Translator(
    locales_dir=Path("./services/locales"),
    default_locale="ru",
    supported=("ru", "en"),
)


def tr(key: str, **params) -> str:
    """Обычный перевод. Локаль берётся из ContextVar."""
    return translator.for_locale(None)(key, **params)


def trn(key: str, count: int, **params) -> str:
    """Перевод с формами множественного числа. Локаль из ContextVar."""
    return translator.for_locale_plural(None)(key, count, **params)


def pick_locale(*candidates: Optional[str]) -> str:
    """Выбор локали по приоритету (например, сохранённая → tg → дефолт)."""
    return translator.pick_locale(*candidates)


@contextmanager
def use_locale(locale: Optional[str]):
    """Временная установка локали через ContextVar (без aiogram)."""
    norm = translator.normalize(locale)
    token = set_current_locale(norm)
    try:
        yield
    finally:
        reset_current_locale(token)
