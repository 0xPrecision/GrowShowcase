from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from keyboards.admin.order_keyboards import (
    change_order_status,
    orders_list_keyboard,
)
from database.crud import get_order_items, get_orders_page
from database.models import Order


def get_order_short_info(order, t) -> str:
    """
    Generates a short order description for displaying in an inline keyboard.
    """
    return t(order.status)


async def show_orders(callback: CallbackQuery, t, page: int, text: str, **_):
    """
    Displays the list of orders with pagination and an inline keyboard.

    :param callback: CallbackQuery — Telegram event object.
    :param page: int — current page number (from 1).
    :param text: str — title or message text.
    :return: None.
    """
    orders, has_next, has_prev = await get_orders_page(page)
    orders_for_kb = [(order.id, get_order_short_info(order, t)) for order in orders]
    if not orders:
        await callback.answer(
            t("order_utils.messages.zakazov-poka-net"), show_alert=True
        )
        return
    await callback.message.edit_text(
        text,
        reply_markup=orders_list_keyboard(orders_for_kb, t, page, has_next, has_prev),
    )


async def admin_show_order_summary(
    event, state: FSMContext, order: Order, order_id: int, t
):
    """
    Universally sends the administrator a detailed order description,
    including all items, total cost, and customer data.
    :param event: CallbackQuery or Message — Telegram event object.
    :param state: FSMContext.
    :param order: Order object.
    :param order_id: int — order ID.
    :return: None.
    """
    await order.fetch_related("user")
    order_items = await get_order_items(order)
    order_info = (
        t("order.info.customer").format(name=order.name)
        + t("order.info.date").format(date=order.created_at.strftime(t("date_format")))
        + t("order.info.items_header")
    )

    for item in order_items:
        price = item.price_at_order * item.quantity
        order_info += t("order.info.item_line").format(
            product=item.product.name,
            qty=item.quantity,
            price=price,
            currency=t("currency"),
        )

    order_info += (
        t("order.info.total").format(total=order.total_price, currency=t("currency"))
        + t("order.info.payment").format(method=order.payment_method)
        + t("order.info.comment").format(comment=order.comment or "-")
    )
    text = t("order_utils.misc.b-detali-zakaza-b").format(
        order_id=order_id, order_info=order_info
    )
    if hasattr(event, "message"):
        await event.message.edit_text(text=text, reply_markup=change_order_status(t))
    else:
        msg = await event.answer(text=text, reply_markup=change_order_status(t))
        await state.update_data(main_message_id=msg.message_id)
