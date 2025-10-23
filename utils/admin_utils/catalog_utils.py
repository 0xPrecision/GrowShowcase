from collections.abc import Awaitable
from typing import List, Tuple

from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from database.models import Product
from keyboards.admin.catalog_keyboards import (
    ask_of_create_product,
    products_list_keyboard,
)
from utils.common_utils import delete_request_and_user_message


def get_product_short_info(product, t) -> str:
    """
    Generates a short string with the main product info for an inline keyboard.

    :param product: Product object.
    :return: String like "Name | Price".
    """
    return f'{product.name} | {product.price} {t("currency")}'


async def get_products_info(
    callback: CallbackQuery,
    t,
    page: int,
    text: str,
    func: Awaitable[Tuple[List["Product"], bool, bool]],
    state: FSMContext,
    **_,
) -> None:
    """
    Generic asynchronous handler for displaying a paginated product list.

    :param callback: CallbackQuery from aiogram.
    :param page: Current page number.
    :param text: Message text.
    :param func: Awaitable returning a tuple (products, has_next, has_prev).
    :param state: FSMContext from aiogram.
    :return: None.
    """
    await delete_request_and_user_message(callback.message, state)
    products, has_next, has_prev = await func
    products_for_kb = [
        (product.id, get_product_short_info(product, t)) for product in products
    ]
    if not products:
        msg = await callback.message.answer(
            t("catalog_utils.messages.tovarov-poka-net-hotite"),
            reply_markup=ask_of_create_product(t),
        )
        await state.update_data(main_message_id=msg.message_id)
        return
    msg = await callback.message.answer(
        text=text,
        reply_markup=products_list_keyboard(
            products_for_kb, page, has_next, has_prev, t
        ),
    )
    await state.update_data(main_message_id=msg.message_id)
