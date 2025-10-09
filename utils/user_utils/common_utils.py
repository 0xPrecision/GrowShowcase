from decimal import Decimal
from typing import List, Tuple

from aiogram.fsm.context import FSMContext
from aiogram.types import Message

def format_product_name(name: str, max_len: int = 20) -> str:
    """
    Truncates the button label if it is too long.
    """
    return name if len(name) <= max_len else name[: max_len - 3] + "..."


def format_price(price) -> str:
    return f"{Decimal(price):,.0f}".replace(",", " ")


async def delete_request_and_user_message(
    message: Message, state: FSMContext, data: dict = None
) -> None:
    """
    Deletes the previous warning (main_message_id) and the user's message.

    :param message: User's Message object.
    :param state: FSMContext.
    :param data: dict with FSM data (if not provided — will be fetched internally).
    """
    if data is None:
        data = await state.get_data()
    main_message_id = data.get("main_message_id")
    if main_message_id:
        try:
            await message.bot.delete_message(message.chat.id, main_message_id)
        except Exception:
            pass
        await state.update_data(main_message_id=None)
    try:
        await message.delete()
    except Exception:
        pass


# def get_order_status_label(status: str, t) -> str:
#     mapping = dict((key, t(label_key)) for key, label_key in ORDER_STATUSES)
#     return mapping.get(status, status)
