from __future__ import annotations

from typing import Optional

from database.models import User, UserLocale


class LocaleRepo:
    @staticmethod
    async def get(user_id: int) -> Optional[str]:
        row = await UserLocale.get_or_none(user_id=user_id)
        return row.locale if row else None

    @staticmethod
    async def set(user_id: int, locale: str) -> None:
        # гарантируем наличие User (если регистрируешь пользователей отдельно — можешь убрать это)
        await User.get_or_create(id=user_id, defaults={"full_name": "", "address": ""})
        await UserLocale.update_or_create(defaults={"locale": locale}, user_id=user_id)
