from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Callable, Dict, Optional
import contextvars

_current_locale: contextvars.ContextVar[str] = contextvars.ContextVar(
    "locale", default="ru"
)


def get_current_locale() -> str:
    return _current_locale.get()


def set_current_locale(loc: str):
    return _current_locale.set(loc)


def reset_current_locale(token) -> None:
    _current_locale.reset(token)


class _SafeDict(dict):
    def __missing__(self, key):
        return "{" + key + "}"


def _ru_pl(n: int) -> str:
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


def _en_pl(n: int) -> str:
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
        base = locale.replace("_", "-").lower().split("-")[0]
        return base if base in self.supported else self.default

    def pick_locale(self, *candidates: Optional[str]) -> str:
        for c in candidates:
            if not c:
                continue
            base = c.replace("_", "-").lower().split("-")[0]
            if base in self.supported:
                return base
        return self.default

    def for_locale(self, locale: Optional[str]) -> Callable[[str], str]:
        # если locale=None — используем локаль из контекста
        def tr(key: str, **vars: Any) -> str:
            loc = self.normalize(locale or get_current_locale())
            return self.translate(key, loc, **vars)

        return tr

    def for_locale_plural(self, locale: Optional[str]) -> Callable[[str, int], str]:
        def trn(key: str, count: int, **vars: Any) -> str:
            loc = self.normalize(locale or get_current_locale())
            return self.translate_plural(key, count, loc, **vars)

        return trn

    def translate(self, key: str, locale: Optional[str], **vars: Any) -> str:
        loc = self.normalize(locale or get_current_locale())
        val = self._resolve(key, loc)
        if val is None:
            return f"[{key}]"
        if isinstance(val, dict):
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
        loc = self.normalize(locale or get_current_locale())
        bundle = self._resolve(key, loc)
        if not isinstance(bundle, dict):
            return self.translate(key, loc, **vars)
        form = _ru_pl(count) if loc == "ru" else _en_pl(count)
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

    def _resolve(self, key: str, locale: str) -> Any:
        d = self._load(locale)
        if key in d:
            return d[key]
        if locale != self.default:
            base = self._load(self.default)
            if key in base:
                return base[key]
        return None
