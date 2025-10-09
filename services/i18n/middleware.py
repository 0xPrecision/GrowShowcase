# ## i18n/middleware.py
from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict, Optional

from aiogram import BaseMiddleware
from aiogram.types import Update

from services.i18n.translations import Translator


def _tg_lang(update: Update) -> Optional[str]:
    if update.message and update.message.from_user:
        return update.message.from_user.language_code
    if update.callback_query and update.callback_query.from_user:
        return update.callback_query.from_user.language_code
    if update.inline_query and update.inline_query.from_user:
        return update.inline_query.from_user.language_code
    if update.my_chat_member and update.my_chat_member.from_user:
        return update.my_chat_member.from_user.language_code
    if update.chat_member and update.chat_member.from_user:
        return update.chat_member.from_user.language_code
    return None


class LocaleMiddleware(BaseMiddleware):
    def __init__(self, translator: Translator, locale_repo):
        self.tr = translator
        self.repo = locale_repo  # services.LocaleRepo

    async def __call__(
        self,
        handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any],
    ) -> Any:
        tg = _tg_lang(event)
        uid = None
        if event.message and event.message.from_user:
            uid = event.message.from_user.id
        elif event.callback_query and event.callback_query.from_user:
            uid = event.callback_query.from_user.id

        saved = None
        if uid:
            try:
                saved = await self.repo.get(int(uid))
            except Exception:
                saved = None

        loc = self.tr.pick_locale(saved, tg)

        # кладём в data
        data["loc"] = loc
        data["t"] = self.tr.for_locale(loc)
        data["tn"] = self.tr.for_locale_plural(loc)
        data["translator"] = self.tr
        data["locale_repo"] = self.repo
        return await handler(event, data)
