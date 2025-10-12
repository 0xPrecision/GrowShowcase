from decimal import Decimal
from typing import List, Tuple

from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from constants import ORDER_STATUSES


def paginate(items: List, page: int, page_size: int) -> Tuple[List, int, int]:
    """
    Generic pagination for any list.

    :param items: List of elements (e.g., products).
    :param page: Current page number (from 0).
    :param page_size: Number of elements per page.
    :return: (List of elements on the current page, total pages, current page number)
    """
    total = len(items)
    total_pages = (total + page_size - 1) // page_size
    start = page * page_size
    end = start + page_size
    items_on_page = items[start:end]
    return items_on_page, total_pages, page


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
