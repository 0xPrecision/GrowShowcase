# i18n/translations.py
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Dict, Optional


class _SafeDict(dict):
    def __missing__(self, key):
        # оставляем нетронутым пропущенный плейсхолдер, чтобы не падать
        return "{" + key + "}"


def _russian_plural(n: int) -> str:
    n = abs(int(n))
    n100 = n % 100
    n10 = n % 10
    if 11 <= n100 <= 14:
        return "many"
    if n10 == 1:
        return "one"
    if 2 <= n10 <= 4:
        return "few"
    return "many"


def _english_plural(n: int) -> str:
    return "one" if abs(int(n)) == 1 else "other"


class Translator:
    def __init__(
        self,
        locales_dir: Path,
        default_locale: str = "ru",
        supported: tuple[str, ...] = ("ru", "en"),
    ):
        self.locales_dir = Path("./services/locales").resolve()
        self.default = default_locale
        self.supported = set(supported)
        self._cache: Dict[str, Dict[str, Any]] = {}

    def _load(self, locale: str) -> Dict[str, Any]:
        locale = self.normalize(locale)
        if locale in self._cache:
            return self._cache[locale]
        path = self.locales_dir / locale / f"{locale}.json"
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            data = {}
        self._cache[locale] = data
        return data

    def normalize(self, locale: Optional[str]) -> str:
        if not locale:
            return self.default
        loc = locale.replace("_", "-").lower()
        # en-US -> en
        base = loc.split("-")[0]
        return base if base in self.supported else self.default

    def pick_locale(self, *candidates: Optional[str]) -> str:
        # ИГНОРИРУЕМ пустые значения, иначе None превращается в default и крадёт приоритет
        for c in candidates:
            if not c:
                continue
            # локально нормализуем без дефолта
            loc = c.replace("_", "-").lower().split("-")[0]
            if loc in self.supported:
                return loc
        return self.default

    def for_locale(self, locale: Optional[str]) -> Callable[[str], str]:
        loc = self.normalize(locale)

        def tr(key: str, **vars: Any) -> str:
            return self.translate(key, loc, **vars)

        return tr

    def for_locale_plural(self, locale: Optional[str]) -> Callable[[str, int], str]:
        loc = self.normalize(locale)

        def trn(key: str, count: int, **vars: Any) -> str:
            return self.translate_plural(key, count, loc, **vars)

        return trn

    def translate(self, key: str, locale: Optional[str], **vars: Any) -> str:
        loc = self.normalize(locale)
        val = self._resolve(key, loc)
        if val is None:
            # падать из-за пропущенного перевода — удовольствие для мазохистов
            return f"[{key}]"
        if isinstance(val, dict):
            # если по ключу лежит объект для плюрализации — берём "other"
            val = (
                val.get("other")
                or val.get("many")
                or val.get("one")
                or next(iter(val.values()))
            )
        try:
            return str(val).format_map(_SafeDict(vars))
        except Exception:
            return str(val)

    def translate_plural(
        self, key: str, count: int, locale: Optional[str], **vars: Any
    ) -> str:
        loc = self.normalize(locale)
        bundle = self._resolve(key, loc)
        if not isinstance(bundle, dict):
            # если разработчик забыл оформить plural-ключ, отдадим обычный translate
            return self.translate(key, loc, **vars)
        form = self._plural_form(loc, count)
        val = (
            bundle.get(form)
            or bundle.get("other")
            or bundle.get("many")
            or bundle.get("one")
        )
        try:
            return str(val).format_map(_SafeDict({"count": count, **vars}))
        except Exception:
            return str(val)

    def _plural_form(self, locale: str, n: int) -> str:
        return _russian_plural(n) if locale == "ru" else _english_plural(n)

    def _resolve(self, key: str, locale: str) -> Any:
        # 1) локаль пользователя
        d = self._load(locale)
        if key in d:
            return d[key]
        # 2) дефолтная локаль
        if locale != self.default:
            base = self._load(self.default)
            if key in base:
                return base[key]
        return None
