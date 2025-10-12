from typing import List

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from utils.common_utils import get_order_status_label
from database.models import Order


def show_orders_keyboard(orders: List[Order], t, **_) -> InlineKeyboardMarkup:
    """
    Creates an inline keyboard for the user_kb's orders list.

    Each order line gets its own button to view details.
    At the bottom — a button to return to the main menu.

    :param orders: List of the user_kb's Order objects.
    :return: InlineKeyboardMarkup — inline keyboard.
    """
    keyboard = [
        [
            InlineKeyboardButton(
                text=t("orders.list.item").format(
                    order_id=order.id,
                    status=t(
                        get_order_status_label(order.status, t)
                    ),  # тут возвращается локализованный текст со смайликом
                ),
                callback_data=f"order_details_{order.id}",
            )
        ]
        for order in orders
    ]
    keyboard.append(
        [
            InlineKeyboardButton(
                text=t("contact_me"),
                url="https://t.me/TGStoreLab",
            )
        ]
    )
    keyboard.append(
        [
            InlineKeyboardButton(
                text=t("user_cart_keyboards.buttons.v-katalog"),
                callback_data="menu_offers",
            )
        ]
    )
    keyboard.append(
        [
            InlineKeyboardButton(
                text=t("order_keyboards.buttons.v-glavnoe-menyu"),
                callback_data="menu_main",
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def order_details_keyboard(t, **_) -> InlineKeyboardMarkup:
    """
    Creates a keyboard for detailed order view.

    Buttons: return to the list of orders and go to the main menu.

    :return: InlineKeyboardMarkup — inline keyboard.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("order_keyboards.buttons.k-spisku-zakazov"),
                    callback_data="menu_orders",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("order_keyboards.buttons.v-glavnoe-menyu"),
                    callback_data="menu_main",
                )
            ],
        ]
    )


def order_confirm_keyboard(t, **_):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("order_keyboards.buttons.oformit-zakaz"),
                    callback_data="confirm_order",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("user_cart_keyboards.buttons.v-katalog"),
                    callback_data="menu_offers",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("order_keyboards.buttons.redaktirovat-dannye"),
                    callback_data="edit_data",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("catalog_keyboards.buttons.otmena"),
                    callback_data="cancel_order",
                )
            ],
        ]
    )
