import inspect
from typing import Callable

from aiogram import Router
from aiogram.types import CallbackQuery, Message

from config_data.env import ADMIN_IDS

router = Router()


def is_admin(user_id: int) -> bool:
    """
    Checks whether the user is an admin by user_id.
    :param user_id: Telegram user ID.
    :return: Tene if admin.
    """
    return user_id in ADMIN_IDS


def admin_only(handler: Callable) -> Callable:
    """
    Decorator to restrict access to admins only.
    Can be applied to any admin handlers.
    """

    async def wrapper(*args, **kwargs):
        event = args[0]
        user_id = (
            getattr(event.from_user, "id", None)
            if hasattr(event, "from_user")
            else getattr(event.message.from_user, "id", None)
        )
        if not is_admin(user_id):
            if isinstance(event, Message):
                await event.answer("❌You haven't admin permission")
            elif isinstance(event, CallbackQuery):
                await event.answer("❌You haven't admin permission", show_alert=True)
            return
        sig = inspect.signature(handler)
        allowed_kwargs = {k: v for k, v in kwargs.items() if k in sig.parameters}
        return await handler(*args[: len(sig.parameters)], **allowed_kwargs)

    return wrapper
