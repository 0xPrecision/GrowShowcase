from decimal import Decimal
from typing import Dict

from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from database.crud import get_cart, get_orders, get_order_by_id, get_order_items
from keyboards.user_kb.user_checkout_keyboards import after_cancellation_kb
from states.user_states.order_states import OrderStates
from keyboards.user_kb.order_keyboards import (
    order_confirm_keyboard,
    show_orders_keyboard,
    order_details_keyboard,
)
from utils.common_utils import (
    delete_request_and_user_message,
    format_product_name,
)


async def show_orders_menu(
    callback: CallbackQuery,
    t,
    state: FSMContext,
    msg_text: str,
) -> None:
    """
    Displays the user's orders menu.
    """
    await delete_request_and_user_message(callback.message, state)

    user_id = callback.from_user.id
    orders = await get_orders(user_id)

    if not orders:
        await callback.message.answer(msg_text, reply_markup=after_cancellation_kb(t))
        return

    text = t("orders.list.header")
    for order in orders:
        text += t("orders.list.items").format(
            id=order.id,
            date=order.created_at.strftime(t("date_format")),
            status=t(order.status),
            currency=t("currency"),
            total=order.total_price,
        )
    text += t("orders.list.footer")
    await callback.message.answer(text, reply_markup=show_orders_keyboard(orders, t))


async def get_order_details(order_id: int, t, **_) -> Dict:
    """
    Get detailed order information by its identifier.

    :param order_id: int — order ID.
    :return: Dict — {"text": description, "keyboard": inline keyboard}.
    """
    order = await get_order_by_id(order_id)
    if not order:
        return {
            "text": t("admin_orders.messages.zakaz-ne-najden"),
            "keyboard": order_details_keyboard(t=t),
        }
    order_items = await get_order_items(order)
    total = sum([item.quantity * Decimal(item.product.price) for item in order_items])
    items_text = "\n".join(
        [
            f'• {format_product_name(item.product.name)} — {item.quantity} x {t("currency")}{item.product.price} = {t("currency")}{item.quantity * Decimal(item.product.price)}'
            for item in order_items
        ]
    )

    text = t("user_orders_utils.misc.b-zakaz-b").format(
        id=order.id,
        created_at=order.created_at.strftime(t("date_format")),
        status=t(order.status),
        items_text=items_text,
        payment=order.payment_method or "-",
        items=items_text,
        currency=t("currency"),
        total=total,
    )

    return {"text": text, "keyboard": order_details_keyboard(t=t)}


async def show_order_summary(message_or_callback, state: FSMContext, t) -> None:
    """
    Displays the order summary to the user_kb with all entered data (supports Cart ORM and dict).
    Provides options to confirm the order or edit the data.
    """
    await delete_request_and_user_message(message_or_callback, state)
    user_id = message_or_callback.from_user.id
    data = await state.get_data()
    cart_items = await get_cart(user_id)
    client = data.get("client_name") or "-"
    pay = data.get("payment_label") or "-"
    comment = data.get("comment") or "-"

    summary = t("checkout.summary.header").format(
        name=client,
        comment=comment,
        payment=pay,
    )

    total = Decimal("0")
    for item in cart_items:
        name = format_product_name(item.product.name)
        qty = item.quantity
        price = Decimal(item.product.price)
        pr_sum = price * qty
        total += pr_sum
        summary += t("checkout.summary.item_line").format(
            name=name, qty=qty, line_total=pr_sum, currency=t("currency")
        )

    summary += t("checkout.summary.total_block").format(
        total=total, currency=t("currency")
    )

    summary += t("checkout.summary.hint")

    if hasattr(message_or_callback, "edit_text"):
        await message_or_callback.answer(
            summary, reply_markup=order_confirm_keyboard(t)
        )
    else:
        await message_or_callback.message.answer(
            summary, reply_markup=order_confirm_keyboard(t)
        )
    await state.set_state(OrderStates.confirm)
