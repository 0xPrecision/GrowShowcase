from __future__ import annotations
from typing import Any, Awaitable, Callable, Dict, Optional
from aiogram import BaseMiddleware
from aiogram.types import Update
from services.i18n.translations import Translator, set_current_locale, reset_current_locale

def _tg_lang(update: Update) -> Optional[str]:
    u = (
        getattr(getattr(update, "message", None), "from_user", None)
        or getattr(getattr(update, "callback_query", None), "from_user", None)
        or getattr(getattr(update, "inline_query", None), "from_user", None)
        or getattr(getattr(update, "my_chat_member", None), "from_user", None)
        or getattr(getattr(update, "chat_member", None), "from_user", None)
    )
    return getattr(u, "language_code", None)

def _uid(update: Update) -> Optional[int]:
    u = (
        getattr(getattr(update, "message", None), "from_user", None)
        or getattr(getattr(update, "callback_query", None), "from_user", None)
    )
    return getattr(u, "id", None)

class LocaleMiddleware(BaseMiddleware):
    def __init__(self, translator: Translator, locale_repo):
        self.tr = translator
        self.repo = locale_repo

    async def __call__(self,
        handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any],
    ) -> Any:
        tg = _tg_lang(event)
        uid = _uid(event)

        saved = None
        if uid:
            try:
                saved = await self.repo.get(int(uid))
            except Exception:
                saved = None

        loc = self.tr.pick_locale(saved, tg)

        token = set_current_locale(loc)
        try:
            data["loc"] = loc
            data["t"] = self.tr.for_locale(None)          # берёт из ContextVar
            data["tn"] = self.tr.for_locale_plural(None)  # берёт из ContextVar
            data["translator"] = self.tr
            data["locale_repo"] = self.repo
            return await handler(event, data)
        finally:
            reset_current_locale(token)