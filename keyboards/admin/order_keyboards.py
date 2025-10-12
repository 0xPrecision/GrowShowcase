from typing import List, Tuple

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from constants import ORDER_STATUSES
from utils.common_utils import format_price


def orders_list_keyboard(
    orders: List[Tuple[int, str]],
    t,
    page: int = 1,
    has_next: bool = False,
    has_prev: bool = False,
    **_,
) -> InlineKeyboardMarkup:
    """
    Keyboard for the orders list.
    :param orders: list of (order_id, short_info)
    :param page: current page
    :param has_next: whether there is a next page
    :param has_prev: whether there is a previous page
    :return: InlineKeyboardMarkup
    """
    buttons = [
        [
            InlineKeyboardButton(
                text=f"#_id {order_id} | {short_info}",
                callback_data=f"admin_order_detail:{order_id}",
            )
        ]
        for order_id, short_info in orders
    ]
    nav = []
    if has_prev:
        nav.append(
            InlineKeyboardButton(
                text=t("catalog_keyboards.buttons.nazad"),
                callback_data=f"admin_orders_page:{page - 1}",
            )
        )
    if has_next:
        nav.append(
            InlineKeyboardButton(
                text=t("catalog_keyboards.buttons.vpered"),
                callback_data=f"admin_orders_page:{page + 1}",
            )
        )
    if nav:
        buttons.append(nav)
    buttons.append(
        [
            InlineKeyboardButton(
                text=t("order_keyboards.buttons.poisk-zakaza"),
                callback_data="admin_search_order",
            )
        ]
    )
    buttons.append(
        [
            InlineKeyboardButton(
                text=t("help_keyboard.buttons.glavnoe-menyu"),
                callback_data="/start_admin",
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def show_orders_for_search(orders, t) -> InlineKeyboardMarkup:
    """
    Creates an inline keyboard for searching and selecting an order from the list.

    :param orders: list of orders (Order), each must have attributes id, user.full_name, total_price.
    :return: InlineKeyboardMarkup — keyboard for displaying found orders.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f'id_#{o.id} | {o.name} | {format_price(o.total_price)} {t("currency")}',
                    callback_data=f"admin_order_detail:{o.id}",
                )
            ]
            for o in orders
        ]
    )


def change_order_status(t, **_):
    """
    Keyboard for changing order status and contacting the customer.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("order_keyboards.buttons.smenit-status"),
                    callback_data="change_status",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("help_keyboard.buttons.zakazy"), callback_data="admin_orders"
                )
            ],
        ]
    )


def status_keyboard(order_id: int, t, current_status: str, **_) -> InlineKeyboardMarkup:
    """
    Keyboard for changing the order status.
    :param order_id: Order ID.
    :param current_status: Current order status.
    :return: InlineKeyboardMarkup
    """
    buttons = []
    for status_code, status_label in ORDER_STATUSES:
        if status_code == current_status:
            continue
        buttons.append(
            [
                InlineKeyboardButton(
                    text=t(status_label),
                    callback_data=f"admin_order_set_status:{order_id}:{status_code}",
                )
            ]
        )
    buttons.append(
        [
            InlineKeyboardButton(
                text=t("catalog_keyboards.buttons.nazad"),
                callback_data=f"admin_order_detail:{order_id}",
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=buttons)
